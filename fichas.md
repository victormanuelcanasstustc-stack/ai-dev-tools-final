1. Style Guides and Rules
Idea principal
Una guía de estilo hace que el código sea consistente y más fácil de leer, revisar y mantener. Las reglas compartidas reducen discusiones repetidas y ayudan a que los cambios sigan convenciones conocidas. Las reglas mecánicas conviene automatizarlas para que las personas se concentren en la lógica y el diseño. Las excepciones deben tener una razón clara y no depender solo de gustos personales.

Aplicación al proyecto
Ruff permite revisar automáticamente convenciones del repositorio. En agent/agent.py encontró un problema de organización de imports y una excepción amplia; en eval/run_eval.py también señaló una excepción amplia. Estos avisos dan puntos concretos para revisar, aunque no todos representan un fallo funcional.

Cambio o decisión técnica
Ejecuté Ruff y guardé los resultados en eval/resultados/ruff_resultados.txt y eval/resultados/ruff_resultados.json. La decisión es revisar cada aviso antes de modificar el código y volver a ejecutar las pruebas después de corregirlo.

Fecha de lectura: 19/10/2026
2. Code Review
Idea principal
La revisión de código comprueba que un cambio sea correcto, entendible y mantenible, y permite compartir conocimiento entre desarrolladores. Debe centrarse en el cambio y en criterios acordados, no en preferencias personales. Las herramientas automáticas ayudan con problemas mecánicos, pero no reemplazan el juicio humano sobre diseño, contexto y consecuencias.

Aplicación al proyecto
En agent/agent.py, la respuesta del modelo se convierte desde JSON y se comprueba que findings sea una lista, pero no se valida un esquema completo de cada hallazgo. En eval/run_eval.py, la evaluación detecta por categoría y no compara semánticamente cada hallazgo con el defecto esperado.

Cambio o decisión técnica
Propongo bloquear cambios por fallos reproducibles de pruebas o vulnerabilidades críticas confirmadas, y advertir sobre estilo o riesgos que necesitan criterio humano. Cada hallazgo del agente debería incluir evidencia, ubicación y explicación. La salida del modelo se trata como una propuesta que debe revisarse, no como verdad automática.

Fecha de lectura: 19/10/2026
3. Static Analysis
Idea principal
El análisis estático examina código sin ejecutar el programa completo. Puede encontrar patrones conocidos de errores, problemas de estilo y riesgos de seguridad de forma rápida y repetible. Su cobertura depende de las reglas y capacidades de la herramienta; por eso, una alerta puede ser un defecto real, una precaución o un falso positivo. Los resultados deben interpretarse con contexto.

Aplicación al proyecto
Se ejecutaron Ruff y Bandit sobre el repositorio. Ruff señaló imports, una excepción amplia y llamadas a subprocess sin un argumento check explícito. Bandit detectó patrones que requieren revisar usos de subprocess y construcción de consultas SQL. Los resultados están guardados en eval/resultados/ruff_resultados.* y eval/resultados/bandit_resultados.*.

Cambio o decisión técnica
Añadí una evaluación separada de los analizadores sobre los 15 casos. Su métrica automática tiene una limitación: contar cualquier alerta en un caso defectuoso como verdadero positivo puede sobreestimar la precisión si la alerta no corresponde al defecto sembrado. Por eso, reporto el detalle por caso y no interpreto esa cifra como prueba de detección semántica perfecta.

Fecha de lectura: 20/10/2026
4. Testing Overview
Idea principal
Las pruebas reducen el riesgo de que un cambio rompa comportamientos existentes. Se necesitan pruebas de diferentes alcances, porque ninguna prueba aislada demuestra que todo el sistema funciona. El conjunto debe ser rápido y fiable para poder ejecutarse con frecuencia. Las pruebas también documentan de forma ejecutable qué comportamiento se espera.

Aplicación al proyecto
tests/test_mcp_server.py comprueba principalmente la estructura del servidor MCP: herramientas, recursos y prompts. tests/test_security.py prueba límites de rutas y truncación de salida. Que estas pruebas pasen no demuestra que el agente detecte correctamente todos los defectos del conjunto de evaluación.

Cambio o decisión técnica
Añadí tres pruebas en tests/test_security.py: rechazo de acceso a .venv, rechazo de .env y truncación de salida larga. La suite ejecutada con python -m pytest -q terminó con 8 pruebas aprobadas. Una mejora pendiente es probar más comportamientos del agente y del servidor, no solo su estructura.

Fecha de lectura: 21/10/2026
5. Unit Testing
Idea principal
Una prueba unitaria comprueba una unidad de comportamiento con una intención clara y resultados verificables. Las pruebas pequeñas suelen ser rápidas y ayudan a localizar la causa de un fallo. Conviene probar el camino correcto, entradas inválidas y límites relevantes. Para ser confiables, no deberían depender de servicios externos ni del orden de ejecución, salvo que eso sea precisamente lo que se prueba.

Aplicación al proyecto
En tests/test_security.py, las pruebas de _safe_path verifican que ciertas rutas no permitidas produzcan ValueError. La prueba de _truncate comprueba que una salida larga se recorte y contenga un aviso. Son comprobaciones de comportamiento más concretas que limitarse a comprobar que existen varias herramientas MCP.

Cambio o decisión técnica
Añadí casos para .venv, .env y salida larga. Las pruebas comprueban propiedades relevantes del resultado en lugar de depender de detalles irrelevantes. No afirmo que toda la lógica esté cubierta: la suite sigue siendo pequeña frente a todas las rutas del agente y del servidor.

Fecha de lectura: 21/10/2026
6. Continuous Integration
Idea principal
La integración continua automatiza comprobaciones al subir commits o abrir solicitudes de cambio. Ayuda a detectar fallos pronto y produce un resultado repetible. Para que sea útil, debe ser confiable, razonablemente rápida y señalar o bloquear cambios que no cumplan las condiciones acordadas. Tener un archivo de configuración no basta: también hay que verificar que el flujo se ejecute realmente.

Aplicación al proyecto
.github/workflows/ci.yml se ejecuta en push, pull_request hacia main o master, y manualmente. Usa Ubuntu, configura Python 3.11, instala requirements.txt y ejecuta python -m pytest -q. La ejecución se comprobó en GitHub Actions y apareció en verde.

Cambio o decisión técnica
Corregí la instalación para que los comandos se ejecuten por separado y mantuve explícito el paso de pruebas. El commit de esta corrección es 56767c6 (Fix GitHub Actions workflow). Como mejora posterior, incorporaría Ruff y Bandit al flujo y acordaría qué niveles de alerta deben bloquear un cambio.

Fecha de lectura: 22/10/2026
7. Large-Scale Changes
Idea principal
Los cambios grandes necesitan planificación para que sean seguros y fáciles de revisar. Es preferible dividir una transformación amplia en pasos pequeños y verificables, en vez de mezclar muchos cambios de comportamiento. Las herramientas automáticas ayudan con modificaciones repetitivas, pero el resultado debe validarse con pruebas y revisión. Los commits pequeños y claros facilitan entender y revertir cambios.

Aplicación al proyecto
La corrección de CI se mantuvo separada de las pruebas de seguridad y de los resultados de analizadores. El historial permite identificar intenciones distintas, por ejemplo c0acfd8 para pruebas de seguridad y 56767c6 para corregir el flujo CI.

Cambio o decisión técnica
Mantuve la corrección de CI en un commit separado. Para cambios futuros, revisaré git diff, ejecutaré las pruebas pertinentes y crearé un commit con un mensaje que describa una sola intención. Los identificadores citados deben coincidir con el historial final del repositorio.

Fecha de lectura: 22/10/2026
8. Documentation
Idea principal
La documentación debe permitir que otra persona entienda el propósito del sistema, lo ejecute y conozca sus límites sin depender de explicaciones privadas del autor. También necesita mantenimiento: comandos desactualizados y afirmaciones que ya no coinciden con el comportamiento real pueden causar errores. Es importante distinguir entre lo que está implementado, lo que se probó y lo que solo se propone como mejora.

Aplicación al proyecto
El README.md describe la variante con Groq, el modelo, las herramientas MCP, la instalación y la evaluación. También reconoce límites como la evaluación por categoría y la falta de una orquestación completa de herramientas MCP. Debe coincidir con el flujo CI, las pruebas y los archivos de resultados existentes.

Cambio o decisión técnica
La decisión es mantener comandos reproducibles para instalar, probar y evaluar; enlazar resultados guardados; y explicar las limitaciones de las métricas. Antes de entregar, comprobaré que las rutas citadas existan y que la documentación no presente como implementadas funciones que solo están descritas en el prompt del agente.

Fecha de lectura: 23/10/2026