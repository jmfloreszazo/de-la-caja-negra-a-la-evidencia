# Respuesta tardía del core superada por la recuperación concurrente: prueba TCP local real

**5 de noviembre de 2026 · issue #30 · experimento nativo acotado con `.NET 10 + dos PostgreSQL`.** [English](channel-held-ack.en.md) · [Prueba anterior de TCP loopback](channel-loopback-transport.es.md) · [Contrato del laboratorio](../../lab/channels/CONTRACT.md).

## Por qué no basta con un único reintento satisfactorio

El laboratorio TCP anterior [#100](../../evidence/runs/CHANNEL-LOOPBACK-TCP.es.md) demostró que perder la respuesta del core no significa necesariamente que la transferencia fallara. Pero sus consultas y reintentos se hacían secuencialmente, **después** de que el proxy descartara o retrasara la respuesta original. Eso deja otro riesgo: mientras la respuesta del emisor sigue retenida, varios clientes, terminales o gateways pueden intentar recuperar o repetir **la misma operación**.

La prueba nueva utiliza un cliente TCP real, un proxy efímero en loopback y el API **.NET 10** existente con su PostgreSQL financiero. El proxy transmite un `POST /transfer` ficticio utilizando el `operationId` duradero original, **observa HTTP 200 después del COMMIT de la base** y retiene la respuesta antigua mediante una barrera acotada. El cliente inicial recibe un timeout real. Antes de liberar el ACK, el driver consulta el estado de la operación original, lanza **ocho peticiones HTTP concurrentes con el mismo ID e idéntica intención** y añade una **novena petición contradictoria**: el mismo ID pero diferente importe.

Solo después de comprobar los resultados concurrentes y el estado SQL de lectura se libera la respuesta original. En este único host, los eventos se ordenan mediante `time.monotonic_ns`, por lo que el oráculo puede contrastar el orden de manera reproducible. Ese reloj **no** permite comparar directamente eventos físicos ocurridos en máquinas o redes bancarias independientes.

## Contrato de aceptación y controles negativos

| Momento | Observación original o independiente | Invariante exigido |
| --- | --- | --- |
| Respuesta del emisor retenida | Proxy reenvía POST y lee HTTP 200; SQL ya tiene una operación COMMITTED, dos apuntes y un outbox | El efecto **ya existe**, aunque el cliente no recibió éxito |
| Timeout del primer cliente | HTTP cliente informa `UNKNOWN`; no se ha liberado el ACK | No convertir timeout en rechazo, reverso o dinero disponible |
| Consulta al propietario | `GET /operations/{originalId}` devuelve `COMMITTED` | Conservar el ID del origen |
| Ocho reintentos concurrentes | Todos devuelven `COMMITTED`, `duplicate=true`, `postedCents=6000` | Persisten **una sola operación, dos apuntes y un outbox** |
| Petición contradictoria | El core responde `ID_CONFLICT` al mismo ID con otro importe | La idempotencia debe ligar **identidad e intención** |
| Liberación del ACK antiguo | Se registra que la recuperación terminó **antes** de liberar el mensaje anterior | La respuesta tardía no crea otro COMMIT |
| Auditoría SQL de cierre | Oráculo independiente comprueba conservación, proyección, postings, holds, outbox, identidad y dispositivo | No ocultar dobles efectos con un saldo total coincidente |

El [verificador independiente](../../scripts/check_channel_transport.py) inspecciona el testigo TCP y sus timestamps, el ID original ofrecido, **las ocho respuestas HTTP reales** y no solo un indicador declarado, el intento con importe incorrecto y su rechazo, y snapshots SQL tanto anteriores al reintento como anteriores a liberar el ACK. Las [pruebas adversariales](../../scripts/test_channel_transport_evidence.py) deben detectar un ACK liberado prematuramente, menos reintentos, banderas de duplicación falsas, otro ID, apuntes extra, rechazo fingido y tiempos contradictorios.

La nueva prueba se llama `tcp-held-reply-concurrent-recovery`. El driver alcanza **14 casos nativos** (diez originales y cuatro intervenciones de TCP local), **18** controles independientes de seguridad del proxy y **27** comprobaciones de evidencias, incluyendo negativos. Son objetivos de ejecución hasta verificar su correspondiente Actions original.

## Qué no demuestra

El incremento prueba concurrencia de clientes **en sockets reales de localhost** contra .NET y PostgreSQL, pero no certifica un switch, protocolo ISO 8583, cajero real, partición WAN entre hosts, CICS/Db2, retención productiva de identificadores, conciliación bancaria, journal físico, fencing real del host antiguo ni una autorización de cutover. Las dos bases siguen compartiendo **un mismo dominio de fallo**. El fabricante, procesador y banco pueden imponer reglas de identidad, timeout y reintentos diferentes.

Esto es una prueba de **corrección ante una carrera concreta**, no un benchmark de MIPS, capacidad ni HA. Ocho clientes locales no permiten extrapolar rendimiento bancario ni asegurar exactly-once físico. No se concede permiso de *stand-in*, cargo, reverso o dispensación automática. TODM **G2 INCONCLUSIVE / G6 BLOCK**, E2 `partially_verified`; #30 abierto, #53 congelado y sin nueva release ni despliegue bancario.
