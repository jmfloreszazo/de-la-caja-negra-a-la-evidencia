**Español** · [English](../../en/part-2-archaeology-and-authority/07-legacy-archaeology-assisted-by-agents.md)

[← Capítulo 6 · REA y la arqueología que deja rastro](06-rea-y-la-arqueologia-que-deja-rastro.md) · [Índice](../README.md) · [Capítulo 8 · El conocimiento del agente y el expediente del sistema →](08-el-conocimiento-del-agente-y-el-expediente-del-sistema.md)

# Capítulo 7 · Legacy Archaeology asistida por agentes

> [!IMPORTANT]
> **Tesis del capítulo.** Una migración con IA empieza mejor con preguntas que con prompts de generación. Los agentes especializados reciben entradas tipadas, producen artefactos comprobables y operan con permisos limitados.

Una migración con IA empieza mejor con preguntas que con prompts de generación. ¿Qué programas modifican esta cuenta? ¿Dónde se decide el interés? ¿Cuántos dialectos, versiones y copybooks hay? ¿Qué ocurre cuando falla la escritura final? ¿Qué cambios llegan por jobs nocturnos? ¿Quién mantiene las tablas de códigos? Responder exige combinar análisis sintáctico, metadatos y observación dinámica.

Propongo una cadena de agentes especializados, bajo un controlador común: **inventario y procedencia**, **parser y grafo de dependencias**, **descubrimiento de reglas**, **observador de ejecución**, **redactor de especificaciones**, **diseñador de arquitectura**, **constructor**, **verificador** y **auditor de drift**. No son nueve chatbots opinando sobre el mismo fichero. Cada uno recibe entradas tipadas, produce artefactos comprobables y opera con permisos limitados.

El analizador de COBOL genera un AST del dialecto real, resuelve copybooks y localiza referencias a datos, CALL, SQL embebido y estructuras de control. No le pediría a un LLM que reemplace al parser. El agente toma el resultado y produce hipótesis sobre intenciones: por ejemplo, «una retirada sobre cuentas bloqueadas retorna un código específico sin modificar estado». Esa hipótesis debe ir acompañada de rutas, posiciones, ejemplos observados y limitaciones. Si la ejecución de producción no puede observarse, documentamos el riesgo y diseñamos pruebas en una copia autorizada.

REA representa una referencia metodológica útil en la parte de investigación con herramientas y evidencia [35, 3]. Para mainframe, su soporte concreto debe evaluarse antes de afirmarlo; no confundiría «inspirado por REA» con «REA analiza nativamente CICS». La arquitectura de integración podría utilizar un contrato neutral como `EvidenceItem`, con hashes, procedencia, cobertura y estado `observed / inferred / unknown`. Eso permite intercambiar hallazgos entre analizadores y agentes sin perder su origen.

## Del arqueólogo al agente

La IA reduce el coste de seguir llamadas, agrupar variables, redactar hipótesis y sugerir escenarios de prueba. Puede generar un grafo de conocimiento y proponer límites de dominios. Pero no debe tener permiso para borrar incertidumbres ni para aprobar sus propias hipótesis. La responsabilidad de un agente investigador acaba donde comienza la autoridad de la especificación. Separar ambos ámbitos será decisivo cuando el sistema procese dinero real.

## Una cadena con permisos, no un coro de chatbots

Cada eslabón de la cadena tiene una entrada, un artefacto de salida y algo que expresamente no puede hacer. La última columna es la que separa un sistema de agentes gobernable de una conversación entusiasta.

| Agente | Recibe | Produce | No puede |
|---|---|---|---|
| Inventario y procedencia | Repositorios, datasets, catálogos | Inventario con hashes y propietarios | Modificar fuentes |
| Parser y grafo | Fuentes con copybooks resueltos | AST, grafo de CALL, COPY y SQL | Inferir intención de negocio |
| Descubrimiento de reglas | Grafo y ejecuciones observadas | Hipótesis con localizadores | Aprobar reglas |
| Observador de ejecución | Entorno autorizado | Entrada, estado, salida y efectos | Ejecutar fuera del mandato |
| Redactor de especificaciones | Hipótesis aprobadas | Especificación, DMN, escenarios | Cambiar la baseline |
| Diseñador de arquitectura | Especificación y restricciones | ADR y opciones comparables | Elegir sin evidencia de capacidad |
| Constructor | Contrato público | Candidato y pruebas propias | Tocar oráculos protegidos |
| Verificador | Candidato fijado y baseline | PASS, FAIL o INCONCLUSIVE | Autorizar la entrega |
| Auditor de deriva | Producción y baseline vigente | Alertas de revisión | Reescribir criterios |

![Figura 7.1 · La cadena de agentes: cada eslabón produce un artefacto y ninguno escribe la baseline.](../../figures/es/agent_chain.png)

*Figura 7.1 · La cadena de agentes: cada eslabón produce un artefacto y ninguno escribe la baseline.*

## La especificación viva

El resultado de esta arqueología no es un PDF congelado. Es un conjunto versionado de archivos de intención, especificación, arquitectura, reglas, decisiones y pruebas: `intent.md`, `spec.md`, `plan.md`, ADR, escenarios Gherkin, tablas DMN y manifests de evidencia. Cada regla debe poder contestar «¿de dónde salió?» y «¿qué test la verifica?». Cada transformación debe poder contestar «¿qué regla aprobada intenta satisfacer?».

No todo el código heredado merece convertirse. El análisis debe identificar rutas muertas, duplicaciones, funciones caducadas y comportamientos que el negocio quiere retirar. Pero la decisión de eliminarlos es una decisión funcional con impacto, no un efecto lateral de una refactorización generada.

> **La responsabilidad de un agente investigador acaba donde comienza la autoridad de la especificación.**

---

[← Capítulo 6 · REA y la arqueología que deja rastro](06-rea-y-la-arqueologia-que-deja-rastro.md) · [Índice](../README.md) · [Capítulo 8 · El conocimiento del agente y el expediente del sistema →](08-el-conocimiento-del-agente-y-el-expediente-del-sistema.md)
