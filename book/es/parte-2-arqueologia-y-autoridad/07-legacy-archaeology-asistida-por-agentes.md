**Español** · [English](../../en/part-2-archaeology-and-authority/07-legacy-archaeology-assisted-by-agents.md)

[← Capítulo 6 · REA y la arqueología que deja rastro](06-rea-y-la-arqueologia-que-deja-rastro.md) · [Índice](../README.md) · [Capítulo 8 · El conocimiento del agente y el expediente del sistema →](08-el-conocimiento-del-agente-y-el-expediente-del-sistema.md)

# Capítulo 7 · Legacy Archaeology asistida por agentes

> [!IMPORTANT]
> **Tesis del capítulo.** Una migración con IA empieza mejor preguntando **qué funcionalidades necesita el negocio y qué garantías debe conservar**. ¿Quién autoriza una transferencia? ¿Qué ocurre si se pierde la respuesta? ¿Cuáles son las excepciones y los cierres diarios? Entrevistas, políticas, contratos y pruebas de caja negra autorizadas construyen primero el mapa de capacidades. El análisis sintáctico puede resolver dudas técnicas después, pero no es obligatorio ni determina los dominios de la nueva aplicación.

Una migración con IA empieza mejor con preguntas que con prompts de generación. ¿Qué programas modifican esta cuenta? ¿Dónde se decide el interés? ¿Cuántos dialectos, versiones y copybooks hay? ¿Qué ocurre cuando falla la escritura final? ¿Qué cambios llegan por jobs nocturnos? ¿Quién mantiene las tablas de códigos? Responder exige combinar análisis sintáctico, metadatos y observación dinámica.

Propongo agentes especializados bajo un controlador común: **descubrimiento funcional y procedencia**, **investigación técnica opcional**, **descubrimiento de reglas**, **observador de ejecución**, **redactor de especificaciones**, **diseñador de arquitectura**, **constructor**, **verificador** y **auditor de drift**. No son nueve chatbots opinando sobre el mismo fichero. El negocio determina las capacidades; el legado ofrece observaciones y, cuando sea útil, pistas técnicas. Cada agente tiene entradas, artefactos y permisos limitados.

El descubrimiento funcional produce primero escenarios positivos y negativos, decisiones y responsables. Por ejemplo: «una retirada sobre cuentas bloqueadas retorna un código específico sin modificar estado». La hipótesis requiere política aprobada y observaciones contrastables. **Si una incógnita exige inspección del legado**, se puede utilizar un parser del dialecto COBOL para estudiar AST, CALL, COPY o SQL; esa rama es opcional y no define la arquitectura objetivo. Las incertidumbres quedan abiertas, nunca aprobadas por el agente.

REA representa una referencia metodológica útil en la parte de investigación con herramientas y evidencia [35, 3]. Para mainframe, su soporte concreto debe evaluarse antes de afirmarlo; no confundiría «inspirado por REA» con «REA analiza nativamente CICS». La arquitectura de integración podría utilizar un contrato neutral como `EvidenceItem`, con hashes, procedencia, cobertura y estado `observed / inferred / unknown`. Eso permite intercambiar hallazgos entre analizadores y agentes sin perder su origen.

## Del arqueólogo al agente

La IA reduce el coste de seguir llamadas, agrupar variables, redactar hipótesis y sugerir escenarios de prueba. Puede generar un grafo de conocimiento y proponer límites de dominios. Pero no debe tener permiso para borrar incertidumbres ni para aprobar sus propias hipótesis. La responsabilidad de un agente investigador acaba donde comienza la autoridad de la especificación. Separar ambos ámbitos será decisivo cuando el sistema procese dinero real.

## Una cadena con permisos, no un coro de chatbots

Cada eslabón de la cadena tiene una entrada, un artefacto de salida y algo que expresamente no puede hacer. La última columna es la que separa un sistema de agentes gobernable de una conversación entusiasta.

| Agente | Recibe | Produce | No puede |
|---|---|---|---|
| Descubrimiento funcional y procedencia | Responsables, políticas, canales y observaciones autorizadas | Capacidades y dudas con fuentes | Aprobar reglas |
| Investigación técnica opcional | Fuentes autorizadas, copybooks y metadatos pertinentes | Dependencias con cobertura y procedencia | Elegir límites de negocio |
| Descubrimiento de reglas | Capacidades y resultados observados | Hipótesis y excepciones con fuentes | Aprobar reglas |
| Observador de ejecución | Entorno autorizado | Entrada, estado, salida y efectos | Ejecutar fuera del mandato |
| Redactor de especificaciones | Hipótesis aprobadas | Especificación, DMN, escenarios | Cambiar la baseline |
| Diseñador de arquitectura | Especificación y restricciones | ADR y opciones comparables | Elegir sin evidencia de capacidad |
| Constructor | Contrato público | Candidato y pruebas propias | Tocar oráculos protegidos |
| Verificador | Candidato fijado y baseline | PASS, FAIL o INCONCLUSIVE | Autorizar la entrega |
| Auditor de deriva | Producción y baseline vigente | Alertas de revisión | Reescribir criterios |

![Figura 7.1 · La cadena de agentes: cada eslabón produce un artefacto y ninguno escribe la baseline.](../../figures/es/agent_chain.png)

*Figura 7.1 · Flujo principal desde capacidades y contratos de negocio hasta oráculos TODM y autorización humana G6. Golden Master conserva observaciones por separado; analizar COBOL/JCL es una rama opcional. Ningún agente modifica la baseline aprobada.*

## La especificación viva

El resultado de esta arqueología no es un PDF congelado. Es un conjunto versionado de archivos de intención, especificación, arquitectura, reglas, decisiones y pruebas: `intent.md`, `spec.md`, `plan.md`, ADR, escenarios Gherkin, tablas DMN y manifests de evidencia. Cada regla debe poder contestar «¿de dónde salió?» y «¿qué test la verifica?». Cada transformación debe poder contestar «¿qué regla aprobada intenta satisfacer?».

No todo el código heredado merece convertirse. El análisis debe identificar rutas muertas, duplicaciones, funciones caducadas y comportamientos que el negocio quiere retirar. Pero la decisión de eliminarlos es una decisión funcional con impacto, no un efecto lateral de una refactorización generada.

> **La responsabilidad de un agente investigador acaba donde comienza la autoridad de la especificación.**

---

[← Capítulo 6 · REA y la arqueología que deja rastro](06-rea-y-la-arqueologia-que-deja-rastro.md) · [Índice](../README.md) · [Capítulo 8 · El conocimiento del agente y el expediente del sistema →](08-el-conocimiento-del-agente-y-el-expediente-del-sistema.md)
