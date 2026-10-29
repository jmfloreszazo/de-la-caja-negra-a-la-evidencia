**Español** · [English](../../en/part-7-organization/34-measuring-what-we-do-not-yet-know.md)

[← Capítulo 33 · Plan de modernización: primero una prueba de capacidad, después una apuesta](33-plan-de-modernizacion-primero-una-prueba-de-capacidad.md) · [Índice](../README.md) · [Capítulo 35 · Cuándo NO migraría →](35-cuando-no-migraria.md)

# Capítulo 34 · Medir lo que todavía no sabemos

> [!IMPORTANT]
> **Tesis del capítulo.** El laboratorio muestra un mecanismo; no demuestra que TODM reduzca defectos frente a otras formas de trabajar. Esa pregunta exige un protocolo, una unidad de análisis honesta y la disposición a aceptar resultados negativos.

## Un resultado reproducible no es un estudio comparativo

El laboratorio muestra un mecanismo. No establece que TODM reduzca defectos frente a cualquier otra forma de trabajar. Tampoco establece el ahorro de horas que produciría incorporar agentes a una modernización.

El protocolo público de TODM distingue tres condiciones para estudiar la construcción con agentes: tests acoplados a la implementación, oráculo independiente y oráculo independiente con cualificación por mutaciones. Propone mantener comparables tareas y presupuestos, registrar costes y analizar a nivel de tarea [12]. Esa separación permite formular preguntas que una demo por sí sola no responde.

¿Reduce el oráculo independiente los defectos aceptados? ¿Qué añade su cualificación? ¿Cuántos bloqueos incorrectos produce? ¿Cuánto esfuerzo exige aclarar y aprobar reglas? ¿Qué intentos de modificar el evaluador impiden los permisos reales? Esas preguntas necesitan datos y un diseño previo.

El propio repositorio de TODM lo plantea como un reto abierto: invita a reproducir, falsear, comparar o transferir el método, y acepta los resultados negativos o inconclusos como contribución [2]. Un libro que defiende la evidencia necesita esa puerta abierta.

## La unidad de análisis importa

Si ejecutamos una misma tarea varias veces, tenemos repeticiones de esa tarea. Si inyectamos diez mutaciones en un programa, tenemos diez variantes relacionadas. No deberíamos presentarlas como proyectos independientes para aumentar artificialmente la muestra.

Los resultados deben conservar el agrupamiento: tarea, variante, herramienta, modelo, ejecución y condición. También deben incluir las ejecuciones fallidas y las que quedaron inconclusas. Excluirlas porque ensucian la comparación altera la pregunta que estamos respondiendo.

La regla de parada se fija antes de observar resultados cuando pretendemos una inferencia confirmatoria. Un piloto pequeño puede ser suficiente para encontrar fallos del protocolo o demostrar viabilidad. Que nos permita aprender no lo convierte automáticamente en evidencia generalizable de superioridad.

## Lo que cuesta construir confianza

Mediría el tiempo humano dedicado a preparar datos, aclarar reglas, revisar contratos y resolver discrepancias. Añadiría el consumo del modelo, la ejecución de herramientas, los reintentos y el coste de mantener las pruebas.

También mediría lo que cambia después de entregar: defectos que escapan, tiempo de diagnóstico, recuperación y facilidad para modificar una regla. Si una inversión en oráculos reduce el tiempo de reconstruir por qué se aceptó una versión, ese beneficio merece observarse. Debe medirse, no suponerse.

La arquitectura tampoco queda exenta de evaluación. Un sistema de permisos puede estar bien descrito y mal configurado. Necesitamos intentar modificaciones no autorizadas y observar que el entorno las impide. Una negativa del agente en lenguaje natural no demuestra que carezca del permiso.

## Una conclusión que puede cambiar

Me interesa una metodología capaz de recibir resultados negativos. Si un oráculo resulta demasiado costoso para el riesgo que cubre, habrá que simplificarlo. Si una representación confunde a los revisores de negocio, habrá que cambiarla. Si un agente apenas mejora el trabajo de un flujo determinista, quizá no necesitemos ese agente.

El valor del libro no depende de que todas las hipótesis salgan a favor de TODM. Depende de que el lector pueda distinguir una propuesta de una observación y una observación de una conclusión suficientemente respaldada.

> **El valor del libro no depende de que todas las hipótesis salgan a favor de TODM.**

---

[← Capítulo 33 · Plan de modernización: primero una prueba de capacidad, después una apuesta](33-plan-de-modernizacion-primero-una-prueba-de-capacidad.md) · [Índice](../README.md) · [Capítulo 35 · Cuándo NO migraría →](35-cuando-no-migraria.md)
