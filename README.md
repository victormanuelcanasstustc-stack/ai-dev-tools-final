AI Dev Tools Zoomcamp --- Agente de revisión de código con MCP y Groq
Proyecto final académico desarrollado para el AI Dev Tools Zoomcamp,
utilizando la Variante C: desarrollo sin Claude API, autorizada por
la universidad.
- Proveedor del modelo: Groq API
- Modelo configurado: openai/gpt-oss-20b
- Lenguaje principal: Python 3.11
- Protocolo de herramientas: Model Context Protocol (MCP)
- Repositorio:
  https://github.com/victormanuelcanasstustc-stack/ai-dev-tools-final
1. Descripción
El proyecto implementa una base de agente de IA para apoyar la revisión
de código. Incluye un servidor MCP que expone herramientas de
inspección, recursos y prompts; un cliente que se conecta a un modelo
mediante Groq; un conjunto de 15 casos de evaluación; pruebas
automatizadas; resultados JSON; y un flujo de integración continua en
GitHub Actions.
El objetivo es explorar cómo un agente puede ayudar a identificar
posibles errores de lógica, seguridad, rendimiento y concurrencia, y
cómo se pueden evaluar sus resultados con un conjunto de casos conocido.
Alcance actual: este repositorio es una implementación académica
en evolución. Las métricas del evaluador son preliminares y se
calculan a nivel de caso/categoría; no garantizan que cada hallazgo
coincida exactamente con el defecto esperado. El agente y el servidor
MCP están disponibles como componentes, pero no se debe asumir una
orquestación completa de todas las herramientas MCP sin verificarla.
Las pruebas de seguridad existentes tampoco equivalen a un sandbox
fuerte.

2. Funcionalidades
Servidor MCP
El servidor se encuentra en mcp_server/server.py y ofrece estas
herramientas:
- get_diff: consulta diferencias de Git.
- read_file: lee archivos permitidos del proyecto.
- search_code: busca texto en el código.
- get_file_history: consulta el historial de un archivo.
- run_tests: ejecuta pruebas con un límite de tiempo.
También expone dos recursos:
- project://style-guide: guía de estilo.
- project://risk-catalog: catálogo de riesgos.
Y dos prompts:
- general_code_review: revisión general de código.
- security_review: revisión orientada a seguridad.
Agente y evaluación
- agent/agent.py: cliente/agente básico que utiliza Groq.
- eval/casos/casos.json: conjunto de 15 casos: 4 de lógica, 3 de
  seguridad, 2 de rendimiento, 2 de concurrencia y 4 controles
  limpios.
- eval/run_eval.py: ejecuta la evaluación y calcula métricas.
- eval/resultados/: resultados JSON de ejecuciones guardadas.
Pruebas y CI
- tests/test_mcp_server.py: pruebas del servidor.
- tests/test_security.py: pruebas de validación de rutas.
- .github/workflows/ci.yml: ejecuta pruebas automáticamente en
  GitHub Actions cuando hay push o pull request hacia main o
  master, y permite ejecución manual.
3. Arquitectura general
1. Se proporciona código o un caso de evaluación.
2. El agente solicita una respuesta al modelo configurado en Groq.
3. La respuesta se organiza como resultado de revisión.
4. El evaluador compara la detección con la regla de referencia
   definida en los casos.
5. Se guardan resultados para analizar métricas y tiempos.
La integración completa de las herramientas MCP dentro de un ciclo
autónomo del agente debe considerarse una mejora pendiente si no se ha
validado de extremo a extremo.
4. Requisitos
- Python 3.11 recomendado.
- Git.
- Acceso a una cuenta/proyecto de Groq para ejecutar el agente y la
  evaluación con el modelo remoto.
- Una clave de API de Groq guardada de forma privada.
5. Instalación en Windows PowerShell
Clona el repositorio:
git clone https://github.com/victormanuelcanasstustc-stack/ai-dev-tools-final.git
cd ai-dev-tools-final
Crea y activa un entorno virtual:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Instala dependencias:
python -m pip install --upgrade pip
pip install -r requirements.txt
Ejecuta las pruebas:
python -m pytest -q
Se espera que las pruebas automatizadas terminen sin fallos. El
resultado debe comprobarse en el entorno utilizado.
6. Configuración de Groq
El repositorio incluye .env.example como plantilla. Crea una copia
local llamada .env y completa los valores:
GROQ_API_KEY=TU_CLAVE_DE_GROQ
GROQ_MODEL=openai/gpt-oss-20b
No publiques el archivo .env, no pegues la clave en el código y no la
compartas en capturas, logs o documentos. El .gitignore debe excluir
.env y otros archivos de credenciales. El archivo .env.example debe
contener únicamente valores de ejemplo, nunca una clave real.
7. Ejecutar la evaluación
Desde la raíz del repositorio, con el entorno virtual activo y las
variables configuradas:
python eval/run_eval.py
El script procesa el conjunto de evaluación y guarda un resultado JSON
en eval/resultados/. Revisa el nombre de salida configurado en el
script antes de ejecutar varias veces, porque podría sobrescribir un
resultado anterior. Para una comparación entre modelos, conserva
archivos separados y usa exactamente los mismos casos e instrucciones
para ambos.
8. Métricas
- Precisión: proporción de detecciones positivas que son correctas
  según la regla de evaluación.
- Recall: proporción de casos defectuosos conocidos que el sistema
  detecta.
- F1: media armónica de precisión y recall.
- Tasa de falsos positivos en controles limpios: proporción de
  controles limpios que el sistema marca incorrectamente.
- Tiempo total: duración registrada de la evaluación.
Las métricas actuales son preliminares: el evaluador identifica
detecciones mediante categorías reconocidas y no realiza necesariamente
una comparación semántica exacta de cada hallazgo, ubicación y gravedad.
Los resultados deben interpretarse junto con esta limitación.
9. Seguridad
El servidor incluye controles básicos de rutas y límites para lectura de
archivos. Las pruebas comprueban rutas fuera de la raíz del proyecto,
rutas absolutas externas, rutas con byte nulo y una ruta válida.
Estos controles son útiles, pero no reemplazan un sandbox aislado. La
ejecución de pruebas con subprocess y un timeout no demuestra por sí
sola aislamiento de red, límites de memoria o eliminación de acceso a
secretos. No ejecutes código no confiable en un entorno con credenciales
o permisos sensibles.
10. Integración continua
El workflow .github/workflows/ci.yml:
1. Descarga el repositorio.
2. Configura Python 3.11.
3. Instala las dependencias.
4. Ejecuta python -m pytest -q.
El workflow valida las pruebas existentes. No ejecuta por sí solo una
revisión completa con Groq ni publica comentarios automáticos de
revisión en los pull requests.
11. Evidencias del proyecto
La carpeta evidencias/ contiene capturas de MCP Inspector y registros
de pruebas. La carpeta eval/resultados/ conserva resultados de
evaluación. Para una entrega completa, se recomienda adjuntar capturas
de al menos dos ejecuciones exitosas distintas de GitHub Actions y
mantener identificables los archivos de resultados de cada corrida.
12. Estructura del repositorio
ai-dev-tools-final/
├── .github/
│   └── workflows/
│       └── ci.yml
├── agent/
│   └── agent.py
├── eval/
│   ├── casos/
│   │   └── casos.json
│   ├── resultados/
│   └── run_eval.py
├── evidencias/
├── mcp_server/
│   └── server.py
├── tests/
│   ├── test_mcp_server.py
│   └── test_security.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
La estructura anterior muestra los componentes principales. Puede haber
archivos adicionales en eval/resultados/ y evidencias/.
13. Limitaciones y trabajo futuro
- Integrar las herramientas MCP en un ciclo real del agente y
  comprobarlo de extremo a extremo.
- Separar explícitamente las fases Explore, Analyze y Report.
- Validar las salidas del modelo con un esquema estricto.
- Mejorar la evaluación para comparar tipo, ubicación y evidencia del
  hallazgo con el ground truth.
- Añadir pruebas cuantificadas de prompt injection antes y después de
  la mitigación.
- Aislar run_tests en un contenedor o sandbox con límites reales de
  CPU, memoria, red y permisos.
- Registrar tokens y costes de todas las llamadas, además del tiempo
  total.
- Conservar evidencia de dos ejecuciones verdes de GitHub Actions.
- Comparar dos modelos sobre los mismos 15 casos y documentar
  precisión, recall, F1 y tiempo.
14. Autoría y uso
Proyecto académico realizado por Víctor Manuel Cañas Salazar para el
AI Dev Tools Zoomcamp. Su propósito es educativo y experimental. Los
resultados del agente deben revisarse antes de tomar decisiones sobre
código real.