**Español** · [English](../../en/part-4-patterns/13-before-choosing-a-pattern-identify-the-contract.md)

[← Parte IV · Patrones que sustituyen responsabilidades, no sintaxis](README.md) · [Índice](../README.md) · [Capítulo 14 · Strangler Fig: cambiar el borde antes que el corazón →](14-strangler-fig-cambiar-el-borde-antes-que-el-corazon.md)

# Capítulo 13 · Antes de elegir un patrón, identifica el contrato

> [!IMPORTANT]
> **Tesis del capítulo.** El patrón no se elige por moda, sino por invariante, carga y frontera de fallo. Primero la propiedad que queremos conservar; después el mecanismo mínimo que la satisface fuera de su plataforma original.

En arquitectura solemos utilizar patrones como si fueran piezas de un catálogo: actores, sagas, event sourcing, CQRS, microservicios. El resultado puede acabar siendo una colección de tecnologías modernas sin justificación. Yo invertiría la pregunta. ¿Qué propiedad del sistema antiguo necesito conservar? ¿Qué problema nuevo aparece cuando salgo de su plataforma? ¿Cuál es el mecanismo mínimo que satisface ambas condiciones?

Si una rutina COBOL accede a un dataset en exclusiva durante una ventana batch, su comportamiento no exige necesariamente actores ni Kafka. Tal vez necesite una partición determinista, un único escritor y checkpoint transaccional. Si una operación online requiere actualizar dos tablas con atomicidad, una base relacional y una transacción ACID pueden ser mejores que una saga. Si el sistema debe consultar millones de saldos, quizá necesite una proyección de lectura, no separar prematuramente todas las entidades en microservicios. El patrón no se elige por moda, sino por invariante, carga y frontera de fallo.

## Matriz de sustitución

| Responsabilidad del legado | Patrón candidato | Cuándo sí | Cuándo no basta |
| --- | --- | --- | --- |
| Programa monolítico con reglas mezcladas | Strangler Fig + vertical slice | Separación incremental por capacidad | Si no existe un punto de interceptación seguro |
| Formatos EBCDIC / copybooks | Anti-Corruption Layer + modelo canónico | Interoperabilidad temporal con contrato versionado | Si oculta pérdida de precisión o redondeo |
| Datos compartidos por muchos programas | Ownership de datos por dominio | Cuando puede definirse un escritor responsable | Si persisten escritores ocultos |
| Actualización ACID local | Transaction Script + Unit of Work | Operación con una misma frontera transaccional | Si atraviesa recursos sin transacción común |
| Operaciones por cuenta o póliza | Actor por identidad | Contención localizada y estado encapsulable | Transferencia entre actores o cuenta caliente |
| Eventos hacia otros sistemas | Outbox + Inbox + idempotencia | Publicación fiable después del commit | No convierte sistemas independientes en un ACID global |
| Flujo largo y compensable | Saga / Process Manager | Compensaciones y estados intermedios aceptables | Ledger que exige atomicidad inmediata |
| Lectura masiva de reporting | CQRS / read model | Cargas de consulta diferentes a las de escritura | No sustituye el registro contable autoritativo |
| Batch de millones de registros | Partitioned Batch + checkpoint | Trabajo divisible con claves estables | Dependencias globales y orden estricto |
| Sesiones conversacionales | State Machine + workflow persistente | Estados explícitos y expiración controlada | Contexto implícito aún sin recuperar |
| Reintentos de transacción | Idempotency Key + deduplicación | Reintentos por red, colas y clientes | No corrige efectos externos no idempotentes |
| Semántica de fallos | Bulkhead + timeout + circuit breaker | Aislamiento de degradaciones | No reemplaza reconciliación ni rollback |

La matriz es deliberadamente condicional. No existe un patrón que sustituya «el mainframe» entero. Hay que reconstituir garantías distintas en capas distintas.

Para leer la matriz conviene hacerse siempre las mismas tres preguntas, en este orden. ¿Qué garantizaba el sistema antiguo, aunque nadie lo hubiera escrito? ¿Qué problema nuevo aparece al sacarlo de su plataforma: red, varias instancias, otro motor, otra codificación? ¿Cuál es el mecanismo más simple que resuelve las dos cosas y que podemos probar? Si una propuesta no sabe contestar la tercera, todavía es una preferencia, no un diseño.

> **No existe un patrón que sustituya «el mainframe» entero. Hay que reconstituir garantías distintas en capas distintas.**

---

[← Parte IV · Patrones que sustituyen responsabilidades, no sintaxis](README.md) · [Índice](../README.md) · [Capítulo 14 · Strangler Fig: cambiar el borde antes que el corazón →](14-strangler-fig-cambiar-el-borde-antes-que-el-corazon.md)
