# W01 — Los permisos de lectura los debe imponer PostgreSQL, no una convención de Python

**Nota de investigación e ingeniería · 4 de noviembre de 2026 · Issue #32.** [English](w01-reader-identity.en.md) · [Acta W01 original de 16 casos](../../evidence/runs/W01-PROJECTION.es.md).

## Defecto de alcance identificado después de W01

La primera ejecución W01 demostró que `projection.py` utiliza `SET TRANSACTION ... READ ONLY` contra el origen PostgreSQL sintético. **No acreditó que la identidad de conexión de la aplicación careciera de permisos de escritura.** La conexión al origen usaba el superusuario `postgres` en las 16 pruebas originales. Por tanto, un cambio involuntario, una ruta nueva de código o una credencial filtrada podría modificar saldos. Una transacción SQL de solo lectura es una *propiedad de la sesión*, no una política de mínimo privilegio.

Este incremento refuerza únicamente la **simulación sobre PostgreSQL**. No acredita fencing del origen bancario real, protección ante operadores privilegiados ni equivalencia automática de este mecanismo con CICS/IMS/Db2/VSAM.

## Diseño concreto y controles

- El origen sigue siendo el dueño de `legacy.accounts` y `legacy.clock` y de todas las operaciones financieras en `bf_legacy`, puerto local 55438. La proyección no autoritativa vive en `bf_projection`, puerto 55442.
- **Solo el harness de pruebas** crea el login no privilegiado `w01_reader`, con `USAGE` del esquema `legacy` y `SELECT` exclusivamente sobre `legacy.accounts` y `legacy.clock`. No puede consultar las transacciones/apuntes ni modificar datos financieros, usar `TRUNCATE`, crear triggers, obtener referencias o crear objetos en el esquema.
- La aplicación rechaza una DSN del origen que no use exactamente `w01_reader` o cuya identidad efectiva sea superusuario, pueda crear roles o bases, eludir RLS o posea permisos de mutación financiera. Es **comprobación de privilegios SQL en tiempo de ejecución**, además de un intento real de operación denegada.
- El escritor **exclusivo del harness sintético** dispone de otra DSN, `W01_LEGACY_ADMIN_DSN`, para preparar esquemas, ejecutar transferencias ficticias y consultar el oráculo independiente. `projection.py` no importa ni lee esa DSN; un test lanza la CLI en otro proceso con entorno explícitamente limitado a credenciales de lectura. El propio proceso de test sí tiene credenciales administrativas: **eso no demuestra aislamiento productivo de secretos**.
- Los negativos ejecutan `UPDATE legacy.accounts` incluso tras `SET TRANSACTION READ WRITE`, `UPDATE legacy.clock`, y consulta no autorizada de `legacy.transactions`: PostgreSQL debe devolver `42501 InsufficientPrivilege`. También se rechaza utilizar el superusuario `postgres` como origen de la aplicación. Los 16 casos funcionales anteriores se conservan.
- La operación de reinicio de pruebas verifica **los dos destinos desechables** antes de cualquier `DROP SCHEMA`. Conocer el nombre de una base de datos no basta para limitar una operación destructiva; son obligatorios nombre, puerto, loopback, rol y permiso explícito.
- La CI conserva resultados negativos, logs originales, SHA exacto y JSON. Un PASS de este job significa únicamente **mínimo privilegio verificado sobre el PostgreSQL del laboratorio**, nunca aprobación de migración bancaria.

## Qué todavía no resuelve

Un escritor **privilegiado del origen** puede modificar saldos sin incrementar el reloj. El refresco detecta después el cambio con la misma marca, pero una consulta basada exclusivamente en el watermark no detecta inmediatamente la modificación. Además, una transacción puede confirmar entre la lectura del reloj y el acceso a la proyección: **la respuesta no es linealizable**. No hay CDC continuo, demostración de cierres EOD, HA física, autenticación del cliente, Golden Master aprobado, seguridad de claves o SLO productivos.

Una modernización real debe demostrar que **todos** los escritores online, batch, offline, asíncronos y privilegiados respetan el contrato de versión, autoridad y fencing impuesto por el origen, así como la conciliación independiente de efectos externos. Ver [aceptación de fencing en legacy](../BROWNFIELD_SOURCE_FENCE.es.md) y [limitaciones W01](w01-projection.es.md). La identidad y contraseña `w01_reader` son solo de laboratorio desechable, nunca credenciales productivas.

**TODM G2 continúa `INCONCLUSIVE` y G6 `BLOCK`; no existe PASS bancario global de W01.** Tras ejecutar CI con el SHA exacto, enlazar aquí el run y su artifact sin modificar retrospectivamente la evidencia histórica de 16/16.
