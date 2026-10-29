**Español** · [English](../../en/annexes/annex-f-operational-glossary.md)

[← Anexo E · Catálogo de cien riesgos](anexo-e-catalogo-de-cien-riesgos.md) · [Índice](../README.md) · [Anexo G · Fuentes y alcance de la investigación →](anexo-g-fuentes-y-alcance-de-la-investigacion.md)

# Anexo F · Glosario operativo

| Término | Significado en este libro |
|---|---|
| ACID | Atomicidad, consistencia, aislamiento y durabilidad, dentro de la frontera que soporte el sistema transaccional concreto |
| ACL | Capa anticorrupción: traduce formatos y semántica del legado para que no contaminen el modelo nuevo |
| Actor | Entidad lógica con identidad que procesa mensajes por turnos; en Orleans, un grain |
| ADR | Registro de una decisión de arquitectura, con contexto, alternativas y consecuencias |
| Baseline | Conjunto aprobado y versionado de comportamientos esperados contra el que se juzga un candidato |
| Batch | Trabajo por lotes, a menudo con dependencias, ventanas, checkpoints y reinicios |
| CDC | Captura de cambios de datos desde un sistema origen |
| CICS | Plataforma de procesamiento de transacciones en entornos IBM |
| COMP-3 | Representación decimal empaquetada: dos dígitos por byte y signo en el último nibble |
| Copybook | Fragmento COBOL reutilizable, habitualmente una definición de datos compartida |
| Deadlock | Ciclo de esperas entre transacciones que impide progresar; el motor elige una víctima |
| Fencing | Técnica que permite al almacén rechazar escrituras de un propietario cuya época ya no es vigente |
| Golden master | Observación de referencia del comportamiento existente, útil pero no infalible |
| Idempotencia | Repetir un comando identificable sin repetir su efecto de negocio |
| INCONCLUSIVE | Veredicto que indica que la evidencia no permite concluir; bloquea la entrega por defecto |
| JCL | Lenguaje de control de trabajos que organiza la ejecución batch en z/OS |
| Ledger | Registro contable autoritativo, con trazabilidad de movimientos |
| Mandato | Autorización acotada en alcance, tiempo, presupuesto y acciones para un agente o persona |
| MIPS / MSU | Métricas de capacidad y consumo de contextos mainframe; no equivalen a vCPU |
| Omisión coordinada | Error de medida en el que el generador deja de ofrecer carga mientras el sistema se detiene |
| Oracle Gate | Decisión automatizable que contrasta una obligación con evidencia independiente |
| Oráculo | Mecanismo que responde si un resultado es correcto: ejemplos aprobados, propiedades, tablas de decisión o comparación |
| Outbox | Evento pendiente escrito en la misma transacción que el cambio de estado |
| REA | Reverse Engineer Anything: servidor MCP y CLI que conecta agentes con herramientas de análisis y un contrato de evidencia |
| REDEFINES | Cláusula COBOL que describe la misma región de memoria con otra estructura |
| RPO / RTO | Pérdida de datos y tiempo de recuperación máximos acordados |
| Saga | Coordinación de un proceso distribuido mediante pasos y compensaciones, cuando el negocio lo admite |
| Strangler Fig | Sustitución incremental de capacidades del legado detrás de una fachada |
| Syncpoint | Punto en que CICS confirma o deshace la unidad de trabajo sobre recursos recuperables |
| TODM | Test Oracle-Driven Methodology: aceptación gobernada mediante oráculos independientes y gates G0–G7 |
| VSAM | Familia de métodos de acceso a ficheros en sistemas IBM |
| WLM | Gestión de carga y prioridades en z/OS |

---

[← Anexo E · Catálogo de cien riesgos](anexo-e-catalogo-de-cien-riesgos.md) · [Índice](../README.md) · [Anexo G · Fuentes y alcance de la investigación →](anexo-g-fuentes-y-alcance-de-la-investigacion.md)
