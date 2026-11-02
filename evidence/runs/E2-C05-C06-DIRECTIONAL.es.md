# C05/C06 · Paquetes unidireccionales, respuesta incierta y conciliación SQL

**CI sintética original verificada, 2 de noviembre de 2026. E2 sigue parcialmente verificado.**

La [ejecución #41528812921](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41528812921)
sobre source/checkout `958961906de0ca5d3945d410c64d465ba7d34a3e` superó
ambos jobs: corte en primario `125563418932`, corte en secundario `125563419503`.
Cada caso usa cuatro namespaces distintos en un único host físico. Dos jobs
asignados con el mismo hostname `runnervm48cm3` no acreditan dominios físicos
independientes.

## Originales sin modificar y auditoría independiente

| Dirección bloqueada | Artefacto original | Bytes | ZIP SHA-256 |
| --- | --- | --- | --- |
| primario → secundario | 13180394069 | 22094 | 06d471e856c514b4007f8dc54e1c975de0801a7bc67048d97e71868534d08d6f |
| secundario → primario | 13181810454 | 21662 | 8c865621cae8b72c4d66bb46aabfd1e76e3cbe4ba5ad7364fda3c09148706c73 |

ZIP originales: [primario](e2-c05-c06-primary-original.zip),
[secundario](e2-c05-c06-secondary-original.zip). JSON extraídos sin cambiar bytes:
[primario](e2-c05-c06-primary-original.json), [secundario](e2-c05-c06-secondary-original.json).
Se recalcularon ambos digests y los 64 hashes originales de procedencia de cada
job contra su commit exacto. AccountGrain/Contracts y PgDurableLedger aceptados
siguen intactos. El verificador offline interpreta los registros del PCAP
original, sin confiar solo en el texto decodificado del resumen.

## Resultados medidos

| Observación | Salida del primario bloqueada | Salida del secundario bloqueada |
| --- | --- | --- |
| Intervalo de fallo observado | 46,0143 s | 45,7963 s |
| Paquetes TCP descartados por la regla | 83 | 81 |
| Paquetes permitidos idénticos observados en ambos extremos | 11 | 10 |
| Paquetes de dirección bloqueada en el receptor durante captura | 0 | 0 |
| Orden por gateway primario: mismo ID, importe 31 | Timeout tras envío, ambiguo | Timeout tras envío, ambiguo |
| Orden por gateway secundario: mismo ID, importe 37 | COMMITTED | COMMITTED |
| SQL durante corte, incluida operación inicial | 2 operaciones / 4 apuntes / 2 outbox | 2 / 4 / 2 |
| Catálogos de gestión durante corte | Ambos inaccesibles | Ambos inaccesibles |
| Primeros intentos con respuesta por ambos gateways tras restaurar | 1,6926 s | 1,1831 s |
| Recuperación de silos | Solo restauración de red; mismos contenedores/PID/generaciones | Igual |
| SQL final tras replay, conflicto y orden nueva | 3 / 6 / 3; oráculos 7/7 | 3 / 6 / 3; oráculos 7/7 |

El DROP solo afecta a TCP de los puertos de silo 11150/11151 en OUTPUT de un
namespace. SQL y gateways siguen accesibles desde ambos silos y el cliente.
Fallan ambos intentos de conexión TCP: perder paquetes en una dirección también
elimina el tráfico de retorno que TCP necesita. dumpcap termina con su propio
temporizador de 45 segundos; cada ZIP conserva PCAP, texto decodificado,
identificadores de imagen y reglas exactas. La colocación inicial 8/8 solo usa
métodos de identidad; los clientes financieros no usan hints y cada uno dispone
de un único gateway fijo. Elegir entrada no demuestra qué activación ejecutó
una petición ambigua.

SQL registró independientemente el importe 37 como ganador del ID disputado.
Restauradas las reglas originales, el replay idéntico devolvió
DUPLICATE_COMMITTED, el contenido distinto ID_CONFLICT y una orden nueva
COMMITTED. Se mantuvieron los siete invariantes SQL. Un timeout tras envío no
implica rollback; un catálogo inaccesible no equivale a un catálogo vacío ni
acredita activación exclusiva. Ambas generaciones registradas siguieron Active
en las muestras de membresía; esta ejecución no demuestra muerte/reencarnación
ni activaciones simultáneas.

## Los cuatro jobs fallidos anteriores siguen siendo fallos

La ejecución #41527647221, source `5a260594c159c109cccf49f2f9f8287a37d18e10`,
falló antes de Orleans porque el helper SQL no admitía `c05`. Originales:
[ZIP primario](e2-c05-first-preflight-primary.zip) /
[JSON](e2-c05-first-preflight-primary.json),
[ZIP secundario](e2-c05-first-preflight-secondary.zip) /
[JSON](e2-c05-first-preflight-secondary.json).

La ejecución #41528077816, source `72d93aee4cf148ade04c8e1979bc60d7439bdb75`,
llegó al corte real y a SQL 2/4/2, pero falló porque crun rootless denegó SIGINT
desde el host a tcpdump. Originales, incluidos PCAP incompletos:
[ZIP primario](e2-c05-second-capture-primary.zip) /
[JSON](e2-c05-second-capture-primary.json),
[ZIP secundario](e2-c05-second-capture-secondary.zip) /
[JSON](e2-c05-second-capture-secondary.json).
El verificador fija los cuatro digests y las extracciones originales;
también se auditaron sus 64 hashes de procedencia. La corrección usa un
temporizador nativo, sin ampliar permisos ni debilitar exigencias contables.
Esos fallos no pasan a ser pruebas aprobadas retrospectivamente.

## Límite de aceptación

Se verifican **dos cortes direccionales acotados, conciliación SQL y primeros
intentos con respuesta tras restaurar**. No se acredita activación exclusiva,
ausencia de split brain, fencing, recuperación tras particiones largas,
servicio estable sostenido, HA física independiente, RTO/RPO productivo,
HA PostgreSQL, saturación ni equivalencia MIPS. Los 240 s son un límite del
ensayo, no una promesa; la rama de reinicio asistido no se ejercitó.
El issue #24 sigue abierto para las puertas pendientes de activación/recuperación;
El issue #25 cubre capacidad sostenida. G2 INCONCLUSIVE/G6 BLOCK; #53 congelada.
Sin cambio de release/tag.

[English](E2-C05-C06-DIRECTIONAL.md) · [Protocolo y fuentes fijadas](../../lab/e2_orleans/F10_C05_C06_PROTOCOL.md)

## Sigue abierta una regresión separada de ADO.NET en loopback

La validación amplia #41528813076 sobre el mismo código falló en
`test_multiprocess.py:174`: la prueba ADO.NET de loopback no pudo demostrar
grains alojados en ambos silos antes de SIGKILL. No es un caso C05/C06 ni
un defecto contable probado. El [issue #74](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/74)
sigue la precondición sin resolver y el diagnóstico de fallo pendiente.
El [ZIP original de regresión](e2-c05-loopback-placement-failure-original.zip),
artefacto 13180837720 de 10124 bytes, tiene SHA-256
`55bed14ebac7f582b3d29a9dc13e97c6c75f11a48c64bfdf12a7b18db9fe5332`.
Contiene un PASS válido del proveedor development del paso anterior, bien
identificado por proveedor/nombre de archivo, y ningún éxito ADO.NET. La
[captura decodificada del log de la API](e2-c05-loopback-placement-failure-job.log),
SHA-256 `677bad5736b70539523349d9da3dde0cf8fad5ee0c398d2077e337ca90b7440a`,
conserva el fallo posterior de ADO.NET. Un éxito en otro SHA no explica ni
borra ese negativo.
