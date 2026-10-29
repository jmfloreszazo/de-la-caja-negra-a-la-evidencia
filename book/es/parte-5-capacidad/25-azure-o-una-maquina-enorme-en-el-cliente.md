**Español** · [English](../../en/part-5-capacity/25-azure-or-a-huge-machine-at-the-customer-s-site.md)

[← Capítulo 24 · El benchmark que vale: carga, contención, fallo y coste](24-el-benchmark-que-vale-carga-contencion-fallo-y-coste.md) · [Índice](../README.md) · [Capítulo 25 bis · Infraestructura local, Azure y WAN →](25a-infraestructura-mainframe-local-azure-y-redes-bancarias.md)

# Capítulo 25 · Azure o una máquina enorme en el cliente

> [!IMPORTANT]
> **Tesis del capítulo.** La alternativa no es comprar una máquina brutal: es construir un servicio crítico entero, con su segunda unidad, su recuperación y su gente. Ganar una prueba aislada no basta; hay que satisfacer el contrato completo el peor día que queremos soportar.

## La decisión incluye disponibilidad y operación

Un servidor con mucha CPU, memoria abundante y almacenamiento rápido puede concentrar una carga con menos viajes de red. También puede convertirse en un punto de fallo muy costoso. La alternativa local debe incluir la segunda capacidad necesaria, almacenamiento, red, energía, recuperación, repuestos, licencias y personas que lo operan.

En Azure, el presupuesto incorpora límites de la VM, límites del disco, log, red, réplica y servicio de datos. Microsoft documenta que los límites de IOPS y ancho de banda dependen tanto del almacenamiento como de la VM [27]. Comprar un disco más rápido no garantiza que la instancia pueda aprovecharlo.

La latencia de confirmar el log merece una prueba propia. Si el contrato exige réplica síncrona antes de responder, hay que medir con esa réplica. Si usamos almacenamiento temporal para datos reconstruibles, debemos excluir de ahí cualquier estado cuya pérdida invalide una confirmación.

No hay datos suficientes de tu carga para recomendar ahora una máquina o SKU responsable. Necesitamos primero la huella descrita en el capítulo [22](22-los-mips-no-caben-en-una-conversion-de-vcpu.md) y un conjunto representativo ejecutable. El resultado de esta fase sería una lista corta de configuraciones candidatas y un presupuesto para contrastarlas.

## Tres configuraciones, un protocolo

Compararía un escenario **Azure** (compute, base transaccional y red especificados), uno **on-premises potente** (CPU, RAM, NVMe, red y redundancia definidos) y, si procede, uno **híbrido** que mantiene el core mientras extrae dominios. No utilizaría nombres comerciales como sustitutos de una ficha técnica. La prueba debe repetir la misma carga, distribución de claves, fixtures, política de commit y nivel de disponibilidad. Las cifras por segundo sin persistencia duradera o sin replicación no son comparables con las de un sistema que sí garantiza ambas.

La «supercomputadora» del cliente puede ser excelente para cargas acotadas y baja latencia, pero también necesita alta disponibilidad, discos duraderos, recuperación, gestión de claves, mantenimiento sin parada y un segundo emplazamiento según RPO/RTO. La alternativa no es simplemente comprar una máquina brutal: es construir un servicio crítico entero.

## Tres candidatos de arquitectura

| Candidato | Ventaja a contrastar | Coste o límite a contrastar |
|---|---|---|
| Aplicación modular y una frontera SQL en Azure | Simplicidad transaccional y servicios operados | Log, coste, límites y failover |
| Aplicación particionada con actores o workers | Paralelismo entre entidades | Claves calientes y coordinación cruzada |
| Plataforma local con capacidad de reserva | Localidad y control del entorno | Inversión, redundancia y operación propia |

![Figura 25.1 · Candidato A: aplicación modular y una frontera SQL en Azure, conviviendo con capacidades COBOL conservadas.](../../figures/es/deploy_azure.png)

*Figura 25.1 · Candidato A: aplicación modular y una frontera SQL en Azure, conviviendo con capacidades COBOL conservadas.*

![Figura 25.2 · Candidato C: la «máquina enorme» solo es un candidato serio con su segunda unidad, su réplica y su recuperación ensayada.](../../figures/es/deploy_onprem.png)

*Figura 25.2 · Candidato C: la «máquina enorme» solo es un candidato serio con su segunda unidad, su réplica y su recuperación ensayada.*

Los tres pueden incluir COBOL conservado y C# nuevo. El cambio de plataforma y el de lenguaje no necesitan ejecutarse de una vez. Una coexistencia bien delimitada permite obtener mediciones antes de asumir una sustitución completa.

Mi punto de partida sería mantener la frontera transaccional más sencilla que cubra las garantías y escalar donde la carga permita independencia. Después evaluaría si distribuir estado aporta capacidad suficiente para compensar la coordinación adicional.

## Una arquitectura de referencia: decisiones, no cajas de colores

Propongo una arquitectura de referencia con cinco dominios operativos. Primero, un **adaptador de coexistencia** expone transacciones COBOL autorizadas, traduce los contratos y enruta tráfico. Segundo, una **capa de capacidades de negocio** contiene servicios .NET 10 y, en dominios adecuados, Orleans; otros componentes pueden ser procesos batch. Tercero, un **núcleo de datos transaccional** mantiene el ledger y las reglas de commit. Cuarto, una **capa de integración fiable** usa outbox, inbox, colas y proyecciones. Quinto, una **capa de evidencia y gobierno** ejecuta oráculos, observa drift y controla la entrega.

No asumiría Kubernetes por defecto. Una aplicación con poca variabilidad, carga bien conocida y una única base de datos puede operar eficientemente en VMs o bare metal. Azure App Service, AKS, contenedores, VMs y Azure Local tienen distintos compromisos de operación; la elección responde a SLO, equipo y restricciones, no al afán de ser cloud native. Lo mismo ocurre con Cosmos DB frente a SQL: la distribución global no compensa perder una frontera transaccional que el negocio necesita. Para ciertos ledgers, un motor relacional ACID es la opción más directa.

La arquitectura tiene una **regla de unicidad**: ninguna responsabilidad crítica puede quedar ambigua. Un componente aprueba comandos; un sistema es autoritativo para cada dato; un gate aprueba cada baseline; una persona o comité autoriza cambios de negocio; una operación registra su idempotency key. En diseños que parecen muy distribuidos pero no resuelven esas responsabilidades, los fallos se desplazan del código a la coordinación.

## Localización de los actores

Si utilizamos Orleans, ubicaría actores por claves de cuenta o contrato para operaciones que se beneficien del aislamiento de identidad. No situaría allí toda la contabilidad sin haber verificado persistencia, transacciones y recuperación. Las transferencias entre cuentas deberían atravesar un boundary contable explícito. Para cargas batch pesadas elegiría workers particionados con checkpoints. Para consultas utilizaría modelos de lectura, sabiendo que pueden retrasarse respecto al ledger. Cada elección tiene una razón falsable y una alternativa.

## Probar el peor día que queremos soportar

El ensayo de aceptación debe combinar carga interactiva y batch si en producción comparten recursos. Debe incluir el volumen y la distribución de datos que producen los planes de consulta relevantes. Una base pequeña que cabe en caché puede esconder un problema que aparece al crecer el working set.

Probaría la pérdida de una instancia cuando el resto ya recibe carga, no únicamente cuando la plataforma está vacía. Si necesitamos sostener el servicio con una unidad menos, la capacidad de reserva se demuestra en esa condición. Lo mismo ocurre con mantenimiento, reconstrucción de índices, backups y recuperación.

También mediría el atasco y su drenaje. Una cola que absorbe un pico puede parecer una solución si solo miramos la ausencia de errores; el servicio sigue incumpliendo si tarda horas en ponerse al día. La edad del mensaje y la latencia desde la intención del usuario deben acompañar al throughput del consumidor.

El criterio de elección no es cuál gana una prueba aislada. Es cuál satisface el contrato completo, con un coste y una capacidad operativa que la organización pueda sostener.

> **La «supercomputadora» del cliente también necesita alta disponibilidad, recuperación, mantenimiento sin parada y un segundo emplazamiento.**

---

[← Capítulo 24 · El benchmark que vale: carga, contención, fallo y coste](24-el-benchmark-que-vale-carga-contencion-fallo-y-coste.md) · [Índice](../README.md) · [Capítulo 25 bis · Infraestructura local, Azure y WAN →](25a-infraestructura-mainframe-local-azure-y-redes-bancarias.md)
