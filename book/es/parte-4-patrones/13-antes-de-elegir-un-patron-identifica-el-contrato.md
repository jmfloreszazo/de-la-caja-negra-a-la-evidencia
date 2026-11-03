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

## Tres correspondencias de plataforma, con contratos de fallo distintos

El [catálogo inicial legible por máquina](../../../research/platform-contracts/catalog.json) y su [guía de alcance](../../../research/platform-contracts/README.md) concretan la matriz anterior. Abarca IBM Z/z/OS, Unisys MCP e integración OS 2200; son tres contextos de plataforma, no implementaciones intercambiables. Lo siguiente propone reemplazos y pruebas de aceptación. Ninguno se ejecutó contra un runtime original del fabricante en este incremento de investigación.

**IBM / CICS y Db2.** Inventariar recursos recuperables y límites reales de unidad de trabajo antes de extraer una API [49][56]. Una transacción SQL candidata puede cubrir recursos dentro de su límite. Si el origen coordina además una cola u otro gestor, introducir outbox puede requerir cambiar con aprobación los estados intermedios observables. Inyectar un fallo entre participantes e inspeccionar ambas historias; los saldos finales por sí solos no prueban que sobreviva la coordinación original.

**Unisys MCP / Enterprise Database Server.** La documentación MCP 21 condiciona SINGLEABORT a `INDEPENDENTTRANS` y asigna la rectificación de la transacción abortada a aplicación/usuario [58]. Obtener, por tanto, opciones DASDL/auditoría antes de diseñar reintentos. El candidato debe repetir la instrucción completa adecuada y conciliar su resultado; repetir solo la sentencia fallida puede omitir efectos previos.

**OS 2200 TIP / ePortal.** El conector ePortal 10 puede reenviar tras reconectar; su guía distingue las sesiones con estado [59]. Recuperar por separado contexto de sesión e identidad financiera. Una conexión nueva no prueba que fallase la instrucción anterior ni autoriza repetir su efecto. Esta fuente documenta un conector, no todo el modelo de recuperación de bases de datos OS 2200.

| Correspondencia | Capas candidatas | Contraejemplo y oráculo necesario |
|---|---|---|
| MF006: límite de recursos CICS | UOW de aplicación; transacción de datos; integración recuperable | Commits separados tras extracción: caer entre efectos y conciliar cada participante |
| MF009: configuración de recuperación MCP | Reintento de aplicación; recuperación del motor; procedimiento operativo | Repetir solo una sentencia pierde trabajo previo: comparar instrucción completa esperada y trabajo no afectado |
| MF010: reconexión/sesión TIP | Adaptador semántico; recuperación de sesión; identidad duradera | Repetir en otra sesión duplica o enruta mal: comparar efecto aceptado, identidad y contexto |

El esquema exige fuente/versión fechada, contrato original, capas candidatas, brecha semántica, fallo de control, oráculo, medidas del cliente e IDs de riesgos. El validador rechaza equivalencias inventadas, fuentes sin documentar y estados de evidencia injustificados. Seis mutaciones del catálogo ejercitan esas comprobaciones. **Son verificaciones de metadatos, no seis pruebas de comportamiento del fabricante.** Los oráculos SQL/ATM existentes pueden orientar el diseño candidato; su éxito no verifica una instalación MCP, OS 2200 o IBM.

## Secuencia de decisión para trabajo síncrono, asíncrono y batch

Comenzar por el plazo de negocio y el propietario duradero. Si el solicitante necesita la decisión final ahora, mantener síncrono el comando autoritativo mínimo y proporcionar recuperación de estado ante respuesta perdida. Si se permite completar después, confirmar aceptación duradera con un estado distinto y correlacionar el resultado final posterior. Una cola cambia entrega y buffering; no concede permiso para aprobar trabajo offline.

Después, identificar atomicidad. Conservar efectos inmediatamente inseparables dentro de un límite transaccional compatible. Utilizar saga solo cuando se permiten cada estado intermedio y su compensación. Un workflow aporta progreso duradero entre pasos; un DAG batch necesita además identidad inmutable de entrada, dependencias, checkpoints y publicación controlada. Ni un scheduler ni un worker por registro acreditan un cierre diario correcto.

Finalmente, elegir ubicación según demanda medida y dominios de fallo. Una proyección puede descargar consultas si explicita su frescura. CDC puede alimentarla, pero no transfiere autoridad de escritura. Los workers horizontales siguen compartiendo límites de base de datos/log/cuentas calientes. Conservar o integrar el motor original cuando se desconoce su contrato, falta un reemplazo demostrado de una recuperación necesaria o una modernización más estrecha ya aporta el valor buscado.

Fujitsu GS21, NEC ACOS, Hitachi VOS y Bull GCOS siguen como descubrimiento sin correspondencias de funciones verificadas en este incremento. NonStop, OpenVMS, IBM i y HP 3000 se marcan aparte como plataformas adyacentes por investigar. Desconocido significa investigación pendiente; no ausente, sin soporte o equivalente. El inventario completo de #28 y sus ejemplos batch/offline/CDC/internacionales siguen pendientes. Esta primera base aporta un formato verificable sin presentar una lista larga sin revisar como investigación terminada.


---

[← Parte IV · Patrones que sustituyen responsabilidades, no sintaxis](README.md) · [Índice](../README.md) · [Capítulo 14 · Strangler Fig: cambiar el borde antes que el corazón →](14-strangler-fig-cambiar-el-borde-antes-que-el-corazon.md)
