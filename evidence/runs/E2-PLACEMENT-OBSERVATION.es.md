# E2 · Cada proveedor fallido debe conservar su propia evidencia

**Controles originales de observación verificados, 3 de noviembre de 2026. E2 sigue parcial.**

La [ejecución #41601478234](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41601478234)
sobre source/checkout `c547c3f34badda0cb57ab0b496917dadb1485b04` superó ambos
controles padre: development `125801005081`, ADO.NET `125801005414`.
Son dos jobs nuevos, cada uno en un host físico, no una prueba entre hosts.

## Artefactos originales sin modificar

| Proveedor | Artefacto original | Bytes | ZIP SHA-256 |
| --- | --- | --- | --- |
| development | 13214437651 | 17676 | 56db17efe633841faee910d62b64f51cc8ee100700a3b2c8489310d557d98fb8 |
| adonet | 13214985556 | 18515 | 1d06e1c7541b5a14f515bf720911302ec72dd3ce0383e042e5fc45f7eb818035 |

ZIP: [development](e2-loopback-observation-development-original.zip),
[adonet](e2-loopback-observation-adonet-original.zip). Resúmenes padre extraídos
sin cambiar bytes: [development](e2-loopback-observation-development-original.json),
[adonet](e2-loopback-observation-adonet-original.json).
Se recalcularon ambos digests y los 69 hashes de procedencia de cada job contra
el commit original exacto. Se comprobaron también por SHA-256 los logs de
silos copiados y los diarios JSONL. Cada ZIP contiene el FAIL del hijo, su
manifest, diario, capturas originales de logs y procedencia exacta.

## Qué se ejecutó realmente

| Observación | development | adonet |
| --- | --- | --- |
| Colocación del primer probe, primario / secundario | 7 / 9 | 10 / 6 |
| Resultado del hijo tras rechazo deliberado del primer probe | FAIL, salida 1 | FAIL, salida 1 |
| Fase del fallo | placement-convergence | placement-convergence |
| IDs financieros originales | 1..16 | 1..16 |
| Invocaciones financieras, órdenes, SIGKILL | 0 / 0 / ninguno | 0 / 0 / ninguno |
| Operaciones / apuntes / outbox independientes | 0 / 0 / 0 | 0 / 0 / 0 |
| Oráculos contables SQL | 7/7 | 7/7 |
| Membresía SQL | No aplica | Ambos miembros con generación Active |
| Estrategia de colocación observada | ResourceOptimizedPlacement | ResourceOptimizedPlacement |
| Eventos del diario | Seis consecutivos, un ID de ejecución | Seis consecutivos, otro ID de ejecución |

El padre habilitó una excepción inmediatamente después del primer probe real
de identidad de las cuentas 1..16. Ambos mapas originales repartieron las
cuentas entre los dos servidores. Esto **no reproduce el fallo unilateral
histórico natural**: comprueba que el registrador conserva el mapa real sin
cambiarlo. Se conservan los PID de servidores y cliente independiente, stdout
y stderr del cliente, membresía y logs de política/arranque. Una observación
inaccesible es un error explícito, no un resultado vacío aprobado.

Como **entrada antigua**, se suministró un PASS development histórico válido,
byte a byte idéntico al del [ZIP de regresión conservado](e2-c05-loopback-placement-failure-original.zip).
No se generó como éxito nuevo. Su SHA-256 es
`a5c3e12d6307101a5d14ebe81cabed4e19882b2932db2288a24cb14277f9ba4d`.
Los manifests nuevos permanecen FAIL y apuntan a sus propios archivos de
fallo; ninguno atribuye aquel PASS a este job. El padre declara
NEGATIVE_CONTROL_VERIFIED, no recuperación ni transacción financiera PASS.

## Alcance y pregunta pendiente

No cambian la aserción estricta de dos PID, las claves originales, los límites
de espera, las llamadas financieras, SIGKILL ni el grain/ledger/política C#
aceptados. El observador opcional mantiene el camino predeterminado del helper
en vuelo. Cada intento normal escribe registros por proveedor/ejecución y,
si tiene éxito, un manifest vinculado a su propio archivo recién escrito.
Las copias de logs son capturas en el instante del fallo, antes de la limpieza.

Se verifican **persistencia de observaciones y procedencia proveedor/resultado**.
No se explica la concentración anterior ni se acredita activación exclusiva,
reproducción espontánea de la anomalía, failover, HA física, recuperación tras
partición larga, capacidad sostenida o aceptación global E2. El issue #74
sigue abierto para investigar la colocación natural. G2 INCONCLUSIVE/G6 BLOCK;
La línea #53 sigue congelada; sin cambio de release/tag.

[English](E2-PLACEMENT-OBSERVATION.md) · [Protocolo](../../lab/e2_orleans/LOOPBACK_OBSERVATION_PROTOCOL.md)
