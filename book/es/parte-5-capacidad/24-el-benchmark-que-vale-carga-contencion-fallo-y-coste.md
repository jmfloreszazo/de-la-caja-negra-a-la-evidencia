**Español** · [English](../../en/part-5-capacity/24-the-benchmark-that-counts-load-contention-failure-and-cost.md)

[← Capítulo 23 · Concurrencia que aprovecha la máquina](23-concurrencia-que-aprovecha-la-maquina.md) · [Índice](../README.md) · [Capítulo 25 · Azure o una máquina enorme en el cliente →](25-azure-o-una-maquina-enorme-en-el-cliente.md)

# Capítulo 24 · El benchmark que vale: carga, contención, fallo y coste

> [!IMPORTANT]
> **Tesis del capítulo.** Un benchmark bancario necesita más de un número: cargas uniformes, sesgadas y mixtas, inyección de fallos, coste y una forma de generar carga que no esconda los atascos. Una mejora de TPS que pierde garantías no es una mejora.

Un benchmark bancario necesita más de un número. Definiría tres familias de cargas. **Uniforme**: operaciones repartidas entre muchas cuentas, favorable a paralelización. **Sesgada**: una pequeña proporción de cuentas concentra gran parte del tráfico, revelando hotspots. **Mixta**: transacciones online, consultas y batch simultáneos, reproduciendo la competencia por CPU y almacenamiento. Las proporciones deben derivarse de telemetría o declararse sintéticas.

Mediría TPS sostenidas y máximas, p50/p95/p99, tiempo batch, tasa de errores, abortos y reintentos, consumo de CPU y memoria, esperas de base, red, IOPS, coste por millón de operaciones y tiempo de recuperación. Las colas importan: una API puede seguir respondiendo rápido a las peticiones que acepta mientras pierde o retrasa las demás. Hay que contabilizar el tráfico ofertado, el completado y el rechazado.

La segunda mitad es **fault injection**: matar el proceso antes y después del commit, cortar conectividad con la base, duplicar mensajes, retrasar respuestas, cambiar de líder, reintentar transferencias, restaurar desde checkpoint y comprobar conciliación. Los resultados se publican con versión de código, especificación de hardware, topología, semilla de datos, scripts y configuración. Un dashboard bonito sin esos detalles es otra demo.

Los agentes podrían optimizar implementación o proponer particiones, pero sus cambios vuelven a pasar exactamente los mismos oráculos. No deben tocar silenciosamente los datos de referencia ni reducir el aislamiento para conseguir más throughput. **Una mejora de TPS que pierde garantías no es una mejora**.

## Del benchmark útil al engañoso

Para la aceptación de capacidad usaría un generador con tasa de llegada controlada y mediría desde el instante programado de envío. Un cliente de circuito cerrado reduce involuntariamente la presión cuando el servidor se ralentiza y puede esconder la acumulación real de trabajo, fenómeno relacionado con la omisión coordinada.

Registraría peticiones ofrecidas, admitidas, confirmadas, rechazadas por negocio, fallidas y pendientes. Los percentiles deben mostrar qué población incluyen. No descartaría timeouts para que mejore el p99. Un throughput alto de rechazos no acredita la capacidad de confirmar transferencias.

Separaría warm-up y medición, repetiría ensayos y conservaría su variabilidad. La carga de recuperación y la mezcla batch tendrían pruebas propias. Solo entonces podríamos afirmar qué arquitectura se acerca al compromiso operativo del mainframe y qué diferencias siguen abiertas.

Es la misma disciplina que me impuse al comparar dos agentes alojados en Microsoft Foundry, uno en .NET 10 y otro en Python: misma región, misma cuota, mismo sobre de recursos y una única variable de verdad, el runtime. Un benchmark que cambia dos cosas a la vez no mide nada, y el «cómo lo he medido» es donde un benchmark se gana o se pierde la credibilidad [45].

## Un ejemplo que se puede ejecutar: la omisión coordinada

La omisión coordinada se entiende mejor viéndola. El laboratorio incluye una simulación determinista, sin red, sin esperas reales y sin aleatoriedad: un servidor con un milisegundo de servicio que se detiene 500 ms una sola vez —piensa en un bloqueo largo, un flush del log o una pausa del recolector—. Lo medimos dos veces. En circuito cerrado, un cliente envía la siguiente petición cuando recibe la respuesta anterior. En circuito abierto, las peticiones se programan a 500 por segundo y la latencia se mide desde el instante en que *debían* enviarse, como hace wrk2 [39].

**Listado 24.1 · tools/coordinated_omission_demo.py** — *Ejecutado · simulación*

```text
$ python3 tools/coordinated_omission_demo.py
Same server, one 500 ms stall at t=4.0s, 1 ms service time.

mode                          req    req/s     p50     p95      p99      max  >100ms
------------------------------------------------------------------------------------
closed-loop (1 client)       9500    950.0     1.0     1.0      1.0    501.0       1
open-loop (500/s)            5000    500.1     1.0   251.0    451.0    501.0     401
```

![Figura 24.1 · El mismo servidor y la misma parada. El circuito cerrado registra el atasco una vez; el circuito abierto cuenta cada petición que esperó detrás de él.](../../figures/es/omission_chart.png)

*Figura 24.1 · El mismo servidor y la misma parada. El circuito cerrado registra el atasco una vez; el circuito abierto cuenta cada petición que esperó detrás de él.*

El circuito cerrado informa de un p99 de un milisegundo y de casi el doble de throughput. No miente sobre las peticiones que midió; miente por omisión, porque su único cliente estaba esperando mientras el servidor estaba parado y dejó de ofrecer carga. El circuito abierto revela que 401 peticiones superaron los 100 ms. Ese es el atasco que vería un cliente real en el cierre de mes.

Es una simulación, no una medición: enseña por qué un ensayo de capacidad debe controlar la tasa de llegada y medir desde el envío programado.

> **Un throughput alto de rechazos no acredita la capacidad de confirmar transferencias.**

---

[← Capítulo 23 · Concurrencia que aprovecha la máquina](23-concurrencia-que-aprovecha-la-maquina.md) · [Índice](../README.md) · [Capítulo 25 · Azure o una máquina enorme en el cliente →](25-azure-o-una-maquina-enorme-en-el-cliente.md)
