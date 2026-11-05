# Recuperación tras TCP real en loopback con .NET 10/PostgreSQL — evidencia acotada

[English](CHANNEL-LOOPBACK-TCP.md) · [Issue #30](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/30) · [Investigación ES](../../docs/research/channel-loopback-transport.es.md) · [CI original](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42034784257).

**5 de noviembre de 2026. Se han ejecutado pérdidas/retardos reales de socket TCP sobre 127.0.0.1, un API .NET 10 desechable y transacciones PostgreSQL. No se prueba un ATM físico, un emisor bancario ni una partición WAN.**

## Campañas originales comprobadas

[Ejecución nativa inicial #42033452330](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42033452330), job `127265416676`, SHA de código/checkout `6b742fdef4d0b2c134b7dc41fbb94c57acd8c599`: **14/14 pruebas del proxy PASS; 13/13 casos del driver nativo PASS; verificador independiente de SQL y socket `PASS_BOUNDED_LIVE_LOOPBACK_TRANSPORT`**. Se preservan los diez casos históricos y se añaden tres intervenciones de transporte diferenciadas. [Extracto original de pruebas](CHANNEL-LOOPBACK-PR100-ORIGINAL-CI-EXCERPT.log).

[Ejecución ampliada #42034784257](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42034784257), job `127269987076`, SHA original código/checkout `1a4effced7b5bad20ef117a3b20d0917a7f5673e`: **14/14 controles de seguridad PASS, 13/13 casos nativos PASS, oráculo SQL/transport PASS y 18/18 verificaciones de evidencia PASS** (un original verdadero y **17 manipulaciones diseñadas para ser rechazadas**). [Extracto con timestamps](CHANNEL-LOOPBACK-PR100-EVIDENCE-MUTANTS-CI-EXCERPT.log).

Los 17 negativos incluyen aparentar una aprobación bancaria/WAN, afirmar que una solicitud descartada sí se envió al core, inventar asientos, fingir respuesta recibida, alterar el COMMIT o el outbox, falsificar idempotencia, modificar saldos conservando su suma, duplicar apuntes y cambiar el SHA del código. **Se mutan copias**, nunca la evidencia original del ejecutor.

## Qué se ha observado de verdad

| Caso | Cliente y socket original | Estado SQL original | Recuperación comprobada |
| --- | --- | --- | --- |
| `tcp-drop-before-forward` | El cliente abre TCP; el proxy recibe el mensaje y emite reset **sin conexión al core**; cliente UNKNOWN | Antes del replay: cero operaciones, apuntes u outbox | Se reutiliza ID original; el **primer** COMMIT crea una operación y dos apuntes |
| `tcp-drop-after-owner-response` | El proxy reenvía; observa HTTP 200 posterior al `CommitAsync` de .NET y resetea al cliente **sin devolver respuesta** | Antes del replay: una operación COMMITTED, exactamente dos apuntes y un outbox | Consulta de estado, retry del ID original con `duplicate=true`, sin segundo cargo |
| `tcp-delay-owner-response` | HTTP 200 ya emitido por core; el proxy retrasa **0,8 s** frente a timeout del cliente de **0,15 s** | SQL confirma el COMMIT, dos apuntes y un outbox antes de repetir | Consulta y replay del ID original; sin segunda transferencia |

El estado final ficticio en los tres casos es **4.000 / 16.000 / 0 céntimos** en cuentas 1, 2 y 3. Hay una única transferencia, dos apuntes compensados y un outbox; el oráculo financiero independiente responde PASS. Son **transferencias digitales inventadas**, no dispensaciones. El proxy archiva huella SHA-256 y etapas TCP, no los cuerpos HTTP originales. El driver conserva observaciones HTTP, estado SQL y logs de aplicación/dispositivo en el artifact.

GitHub publicó el artifact inicial `13417117169` (21.334 bytes), SHA-256 `433e46a9c72b87634d3b3c966ecb27f00dc981d663ef22c00e6e9a323fdc5eec`, y el ampliado `13418031808` (21.972 bytes), SHA-256 `c794a6739fe050d69df22de37f8883c1280b88dd03fd7131a84be34952939118`, con caducidad inicial 3 de febrero de 2027. **Son hashes informados por GitHub; no se han descargado y recalculado de manera independiente los ZIP.** Los originales completos y snapshots se conservan en esos artifacts. El [registro JSON](channel-loopback-pr100-original-ci-summary.json) distingue su procedencia.

## Límite científico

Esto demuestra manipulación **real de sockets localhost** alrededor de .NET y PostgreSQL, **no** inyección de pérdida de paquetes mediante `tc netem`, fallos entre hosts, WAN remota, HA física, ATM, switch, emisor, ISO 8583, IBM CICS/Db2 o dispensador. El core y las dos bases comparten **un mismo dominio de fallo**. La política de idempotencia, consulta y replay es de nuestra maqueta, no una norma bancaria certificada.

Un timeout por sí solo no demuestra que el servidor no confirmara la transacción, y cambiar su ID puede causar un duplicado. El oráculo SQL demuestra un alcance cerrado y desechable, no todos los escritores reales de un banco. Quedan pendientes logs originales firmados, política aprobada, reconciliación de efectivo y red, fencing, infraestructura independiente y pruebas de cortes reales. **TODM G2 INCONCLUSIVE / G6 BLOCK**, E2 `partially_verified`; #30 y #58 abiertos, #53 congelado. Sin nueva release ni autorización de despliegue.
