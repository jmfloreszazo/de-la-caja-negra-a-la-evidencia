**Español** · [English](../../en/part-5-capacity/22-mips-do-not-fit-in-a-vcpu-conversion.md)

[← Parte V · Capacidad: MIPS, concurrencia y plataforma](README.md) · [Índice](../README.md) · [Capítulo 23 · Concurrencia que aprovecha la máquina →](23-concurrencia-que-aprovecha-la-maquina.md)

# Capítulo 22 · Los MIPS no caben en una conversión de vCPU

> [!IMPORTANT]
> **Tesis del capítulo.** Una cifra de MIPS contextualiza un entorno; no es una cantidad de trabajo de negocio que podamos repartir entre núcleos x86. La comparación que sirve se expresa en operaciones confirmadas, latencias por clase, ventanas batch y tiempos de recuperación.

## Qué estamos intentando igualar

La pregunta que más me preocupa al sacar una carga de un mainframe no es si el nuevo programa compila. Es si podrá sostener la operación cuando lleguen el cierre, el pico de actividad y un fallo al mismo tiempo. El sistema anterior puede llevar años resolviendo esa combinación con una integración que la aplicación apenas hace visible.

Una cifra de MIPS ofrece una referencia sobre un entorno. No representa una cantidad universal de trabajo empresarial que podamos repartir entre vCPU de otra arquitectura. IBM explica que sus relaciones LSPR dependen de cargas y configuraciones concretas, y que I/O, software y características del trabajo pueden cambiar los resultados reales [14]. Utilizaría esa referencia para contextualizar capacidad, nunca como una tabla de compra de servidores x86.

La comparación que necesito tiene unidades de negocio: transferencias confirmadas por segundo, consultas con su latencia, pólizas procesadas dentro de la ventana, incidencias pendientes y tiempo de recuperación. Cada medida debe conservar la semántica. Confirmar una transferencia en memoria y devolver HTTP 200 no equivale a confirmar su registro durable con la política de réplica acordada.

Tampoco una media cuenta toda la historia. Podemos aumentar el throughput total y empeorar mucho la experiencia de una cuenta con alta contención. Necesitamos percentiles por tipo de operación, errores, rechazos de negocio, reintentos y edad de la cola. El pico de una clase no debe esconderse dentro del promedio de otras más baratas.

## Lo que cambia cuando cambiamos de arquitectura

No propondría un dimensionamiento diciendo «un MIPS son tantas operaciones por segundo en x86». MIPS es una métrica dependiente de la plataforma, de la definición utilizada y de las características del workload; MSU se utiliza en entornos IBM para mediciones y capacidad/licenciamiento, pero tampoco equivale a una unidad universal de CPU cloud. La relación entre instrucciones, latencia e I/O cambia cuando transformamos la arquitectura. Un `CALL` local puede acabar siendo HTTP. Un acceso DB2 en el mismo entorno puede convertirse en red y TLS. Una optimización de decimales empaquetados puede convertirse en otra representación y otro vector de ejecución.

## Recuperar una huella de carga

Antes de dimensionar pediría al equipo del mainframe una captura representativa de la actividad y sus condiciones. IBM documenta herramientas RMF y registros de monitorización CICS que permiten observar recursos, CPU y esperas por transacción [15]. El equipo de sistemas debe interpretar esos datos: una LPAR con capacidad limitada, una mezcla particular de motores y unas prioridades WLM concretas no se resumen en la CPU nominal de la máquina.

La huella debe distinguir operaciones interactivas, batch, consultas y trabajo delegado a otros subsistemas. También debe identificar el volumen de datos activo, las distribuciones de acceso, las cuentas calientes y los compromisos entre procesos. La hora de mayor CPU no tiene por qué ser la de peor latencia.

Conservaría días normales y periodos críticos, según el negocio: cierre, fin de mes o eventos excepcionales. No pediría un plazo universal de observación. Pediría evidencia de que el conjunto cubre las situaciones para las que vamos a comprometer capacidad.

Un inventario útil para dimensionar contiene lo siguiente:

| Dimensión | Evidencia que necesitamos | Decisión que permite |
|---|---|---|
| Trabajo | Tasas por operación y tamaños de petición | Mezcla y generador de carga |
| CPU | Consumo y distribución por clase | Presupuesto de cálculo |
| Espera | Bloqueos, log, I/O y dependencias | Cuello de botella prioritario |
| Datos | Volumen activo, cardinalidad y sesgo | Memoria e índices |
| Batch | Dependencias, particiones y duración | Camino crítico y ventana |
| Recuperación | Fallos, reinicio, RTO y RPO acordados | Redundancia y pruebas |

![Figura 22.1 · Del mainframe a una configuración candidata: la huella de carga alimenta un modelo de demanda que solo un ensayo puede confirmar.](../../figures/es/capacity_flow.png)

*Figura 22.1 · Del mainframe a una configuración candidata: la huella de carga alimenta un modelo de demanda que solo un ensayo puede confirmar.*

## Un cálculo que ayuda sin fingir precisión

Supongamos, como ejercicio, que una prueba en el destino mide un milisegundo de CPU de aplicación por operación y que necesitamos 8 000 operaciones por segundo. Esa demanda consume ocho segundos de CPU por segundo. A un objetivo ilustrativo del sesenta por ciento de utilización necesitaríamos aproximadamente catorce cores efectivos para esa parte paralelizable de la aplicación.

El cálculo no incluye todavía base de datos, recogida de memoria, cifrado, instrumentación, desequilibrios, reservas o redundancia. Tampoco permite sustituir el milisegundo medido en destino por un milisegundo observado en z/OS. El objetivo es construir un modelo que podamos corregir con mediciones, no aparentar un dimensionamiento terminado.

Otra relación útil conecta caudal, duración media y trabajo en curso. A 10 000 operaciones por segundo y 25 milisegundos de duración media estable, hay unas 250 operaciones en curso de media. No significa que debamos abrir 250 conexiones SQL. La duración cambia cuando aumenta la contención, y parte de ese trabajo puede estar esperando fuera de la base de datos.

Separar demanda de CPU, espera e I/O evita comprar potencia para resolver una cola causada por un recurso serializado. Un servidor mayor puede ser una solución; primero necesitamos demostrar qué recurso está limitando la capacidad.

> **Un servidor mayor puede ser la solución. Primero hay que demostrar qué recurso está limitando la capacidad.**

---

[← Parte V · Capacidad: MIPS, concurrencia y plataforma](README.md) · [Índice](../README.md) · [Capítulo 23 · Concurrencia que aprovecha la máquina →](23-concurrencia-que-aprovecha-la-maquina.md)
