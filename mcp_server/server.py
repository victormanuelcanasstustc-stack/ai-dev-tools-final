from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI Code Review Assistant")

# La raíz queda fijada al directorio del proyecto.
PROJECT_ROOT = Path(
    os.environ.get("PROJECT_ROOT", str(Path(__file__).resolve().parent.parent))
).resolve()

MAX_FILE_BYTES = 100_000
MAX_OUTPUT_CHARS = 12_000
MAX_SEARCH_RESULTS = 50
MAX_TEST_SECONDS = 30

IGNORED_DIRS = {
    ".git", ".venv", "venv", "_pycache_", "node_modules",
    ".pytest_cache", "dist", "build"
}

SECRET_NAME_PATTERNS = (
    re.compile(r"^\.env($|\.(?!example$))", re.IGNORECASE),
    re.compile(r".*\.(pem|key|p12|pfx)$", re.IGNORECASE),
    re.compile(r".(secret|credential|password).", re.IGNORECASE),
)

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
    ".toml", ".md", ".txt", ".html", ".css", ".sh", ".ps1",
    ".ini", ".cfg", ".sql"
}


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[salida truncada por límite de tamaño]"


def _is_secret_name(name: str) -> bool:
    return any(pattern.fullmatch(name) for pattern in SECRET_NAME_PATTERNS)


def _safe_path(relative_path: str) -> Path:
    """Resuelve rutas dentro del proyecto y rechaza escapes y secretos."""
    if not relative_path or "\x00" in relative_path:
        raise ValueError("La ruta está vacía o no es válida.")

    candidate = (PROJECT_ROOT / relative_path).resolve()

    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError:
        raise ValueError("Acceso denegado: la ruta sale de la raíz del proyecto.")

    relative_parts = candidate.relative_to(PROJECT_ROOT).parts

    if any(part in IGNORED_DIRS for part in relative_parts):
        raise ValueError("Acceso denegado a directorios excluidos.")

    if any(_is_secret_name(part) for part in relative_parts):
        raise ValueError("Acceso denegado a archivos que podrían contener secretos.")

    return candidate


def _run_git(arguments: list[str], timeout: int = 10) -> str:
    """Ejecuta Git sin shell y siempre dentro de la raíz configurada."""
    result = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
    )

    if result.returncode != 0:
        detail = result.stderr.strip() or "Git devolvió un error."
        return f"ERROR DE GIT: {_truncate(detail, 2000)}"

    return _truncate(result.stdout)


@mcp.tool()
def get_diff() -> str:
    """Obtiene las diferencias Git del proyecto, limitadas en tamaño."""
    try:
        return _run_git(["diff", "--no-ext-diff", "--unified=3", "--"])
    except subprocess.TimeoutExpired:
        return "ERROR: Git superó el tiempo máximo permitido."
    except FileNotFoundError:
        return "ERROR: Git no está instalado o no está disponible en PATH."


@mcp.tool()
def read_file(path: str) -> str:
    """Lee un archivo de texto dentro de la raíz del proyecto."""
    try:
        target = _safe_path(path)

        if not target.is_file():
            return "ERROR: el archivo no existe o no es un archivo regular."

        if target.stat().st_size > MAX_FILE_BYTES:
            return f"ERROR: el archivo supera el límite de {MAX_FILE_BYTES} bytes."

        if target.suffix.lower() not in TEXT_EXTENSIONS and target.name != ".gitignore":
            return "ERROR: extensión de archivo no permitida para lectura."

        content = target.read_text(encoding="utf-8", errors="replace")
        return _truncate(content)

    except (ValueError, OSError) as error:
        return f"ERROR: {error}"


@mcp.tool()
def search_code(query: str) -> str:
    """Busca texto en archivos de código permitidos, con resultados limitados."""
    if not query or len(query) > 200:
        return "ERROR: la búsqueda debe contener entre 1 y 200 caracteres."

    matches: list[str] = []

    try:
        for current, directories, filenames in os.walk(PROJECT_ROOT):
            directories[:] = sorted(
                name for name in directories
                if name not in IGNORED_DIRS and not _is_secret_name(name)
            )

            for filename in sorted(filenames):
                if _is_secret_name(filename):
                    continue

                file_path = Path(current) / filename

                if file_path.suffix.lower() not in TEXT_EXTENSIONS:
                    continue

                try:
                    if file_path.stat().st_size > MAX_FILE_BYTES:
                        continue

                    lines = file_path.read_text(
                        encoding="utf-8", errors="replace"
                    ).splitlines()
                except (OSError, UnicodeError):
                    continue

                for line_number, line in enumerate(lines, start=1):
                    if query.casefold() in line.casefold():
                        relative = file_path.relative_to(PROJECT_ROOT)
                        matches.append(
                            f"{relative}:{line_number}: {line[:300]}"
                        )

                        if len(matches) >= MAX_SEARCH_RESULTS:
                            matches.append("Se alcanzó el límite de resultados.")
                            return _truncate("\n".join(matches))

        return "\n".join(matches) if matches else "No se encontraron coincidencias."

    except OSError as error:
        return f"ERROR durante la búsqueda: {error}"


@mcp.tool()
def get_file_history(path: str) -> str:
    """Consulta el historial Git de un archivo dentro del proyecto."""
    try:
        target = _safe_path(path)
        relative = target.relative_to(PROJECT_ROOT).as_posix()

        return _run_git(
            ["log", "--follow", "--oneline", "-n", "10", "--", relative]
        )
    except (ValueError, OSError) as error:
        return f"ERROR: {error}"
    except subprocess.TimeoutExpired:
        return "ERROR: la consulta del historial superó el tiempo permitido."
    except FileNotFoundError:
        return "ERROR: Git no está instalado o no está disponible en PATH."


@mcp.tool()
def run_tests() -> str:
    """Ejecuta pytest con tiempo limitado y sin shell.

    Ejecuta código de pruebas del propio proyecto. El timeout y el entorno
    reducido son defensas básicas, no un aislamiento completo del sistema.
    """
    test_dir = PROJECT_ROOT / "tests"

    if not test_dir.is_dir():
        return "ERROR: no existe la carpeta tests del proyecto."

    try:
        # Se restringe el entorno heredado; en Windows se conservan variables
        # necesarias para encontrar Python y archivos temporales.
        allowed_keys = ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")
        safe_env = {
            key: os.environ[key]
            for key in allowed_keys
            if key in os.environ
        }
        safe_env["PYTHONDONTWRITEBYTECODE"] = "1"

        result = subprocess.run(
            [
                os.fspath(Path(os.sys.executable)),
                "-m", "pytest",
                "-q",
                "--disable-warnings",
                "--maxfail=5",
                os.fspath(test_dir),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=MAX_TEST_SECONDS,
            env=safe_env,
            shell=False,
        )

        output = (
            f"Código de salida: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
        return _truncate(output)

    except subprocess.TimeoutExpired:
        return f"ERROR: las pruebas superaron el límite de {MAX_TEST_SECONDS} segundos."
    except OSError as error:
        return f"ERROR al ejecutar pytest: {error}"


@mcp.resource("project://style-guide")
def style_guide() -> str:
    """Guía de estilo disponible para el agente."""
    return """
GUÍA DE ESTILO DEL PROYECTO

- Escribir código claro y fácil de mantener.
- Preferir nombres descriptivos y funciones pequeñas.
- Validar las entradas antes de utilizarlas.
- Manejar errores sin ocultar fallos relevantes.
- No guardar claves, contraseñas ni tokens en el repositorio.
- Evitar eval, exec y ejecución de comandos construidos con entradas del usuario.
- Añadir pruebas para cambios de comportamiento.
- Documentar las decisiones importantes y los límites conocidos.
- No afirmar que una prueba pasó si no se ejecutó y verificó.
""".strip()


@mcp.resource("project://risk-catalog")
def risk_catalog() -> str:
    """Catálogo de riesgos que debe consultar el agente."""
    return """
CATÁLOGO DE RIESGOS

1. Seguridad: inyección, secretos expuestos, rutas inseguras y validación
   insuficiente de entradas.
2. Lógica: condiciones incorrectas, límites mal definidos y errores de cálculo.
3. Rendimiento: bucles innecesarios, trabajo repetido y consumo excesivo.
4. Concurrencia y estado: condiciones de carrera, estado compartido inseguro
   y operaciones no atómicas.
5. Calidad de pruebas: casos ausentes, afirmaciones débiles y falsos positivos.

Para cada hallazgo, indicar archivo, línea si se conoce, evidencia,
severidad, categoría y una recomendación concreta.
No inventar ubicaciones ni presentar sospechas como defectos confirmados.
""".strip()


@mcp.prompt()
def general_code_review() -> str:
    """Prompt para revisar código de forma general."""
    return """
Revisa el proyecto con enfoque de ingeniería.
Utiliza las herramientas disponibles para reunir evidencia.
Distingue defectos confirmados de sospechas.
Clasifica los hallazgos por severidad y categoría.
Propón correcciones concretas y no afirmes haber ejecutado pruebas
si no tienes resultados que lo demuestren.
""".strip()


@mcp.prompt()
def security_review() -> str:
    """Prompt para revisar el proyecto con enfoque de seguridad."""
    return """
Realiza una revisión de seguridad defensiva.
Busca rutas inseguras, exposición de secretos, validación insuficiente,
inyección, ejecución de comandos insegura y pruebas sin límites.
No reveles valores de secretos.
Apoya cada hallazgo en evidencia y recomienda una mitigación verificable.
""".strip()


if __name__ == "__main__":
    mcp.run()