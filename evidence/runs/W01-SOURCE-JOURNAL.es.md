# W01 — Experimento original del journal del origen: PASS acotado

**Evidencia: 4 de noviembre de 2026.** [English](W01-SOURCE-JOURNAL.md) · [PR #94](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/94) · [GitHub Actions original #41864738886](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864738886)

## Resultado y procedencia

**`PASS_BOUNDED_SYNTHETIC_TESTS`: 22 de 22 pruebas ejecutadas sobre PostgreSQL real y cero errores inesperados.** Se ha validado un **journal transaccional sintético escrito por el origen del fixture**. Esto **no** equivale a CDC real Db2/VSAM/IMS/CICS, fencing del mainframe, lectura linealizable de saldo ni aceptación bancaria.

| Campo | Valor |
| --- | --- |
| SHA exacto del código y checkout original | `80c45437312030a8abe90e0c3fdaa85a00c3056a` |
| Commit de integración en main | `69bb2e92fbfac66038d6ce1ca3234b020feb2d52` |
| Run / job original | `41864738886` / `126695939112` |
| Artifact GitHub Actions | `13341603193`, `w01-owner-journal-original-not-mainframe-cdc`, 3184 bytes |
| SHA-256 del ZIP informado por GitHub | `3019a6d70d928c71efa206d70d46cf362d85351f896e224debd6063951121806` |
| SHA-256 recalculado del ZIP original descargado | `3019a6d70d928c71efa206d70d46cf362d85351f896e224debd6063951121806` — **COINCIDE** |
| Integridad ZIP | CRC correcto para `test-original.log`, `feed-original.json` y `provenance.txt` |
| Entorno | Python 3.12.16, Podman 4.9.3, PostgreSQL 16.13; dos instancias de servidor en contenedores sobre **un único runner** |
| Caducidad inicial del artifact | 2 de febrero de 2027, sujeta a retención de GitHub |

Se han **descargado e inspeccionado los bytes originales** del ZIP y verificado el SHA-256. El [manifiesto JSON](w01-source-journal-pr94-original-ci-summary.json) preserva el resultado y la procedencia; el [extracto literal con marcas temporales](W01-SOURCE-JOURNAL-PR94-CI-EXCERPT.log) conserva líneas del job original sin ser el ZIP entero. Una ejecución sobre el SHA del PR **no se convierte retroactivamente** en una ejecución del commit de fusión.

## Controles demostrados

La salida original identifica 22 casos `ok`. Entre ellos: COMMIT conjunto del origen con saldos, dos apuntes, outbox, reloj y journal; aborto sin efectos financieros; snapshot inicial MVCC consistente; cursor y saldos del destino confirmados juntos; captura de un COMMIT posterior al snapshot; rechazo de secuencias ausentes, historial eliminado, hash alterado, enlace anterior inválido, imagen previa semánticamente falsa aunque se recalcule su hash y corrupción del destino.

Se ha inyectado un fallo entre la modificación de cuentas y el COMMIT del cursor, comprobándose rollback conjunto y replay posterior. Se han probado permisos SQL `SELECT` del lector, rechazo de superusuario y **ocho escritores concurrentes** sobre cuentas disjuntas. La cadena conserva un orden total mediante bloqueo del reloj: **introduce contención** y no prueba rendimiento productivo. La auditoría de historial completo detecta modificaciones privilegiadas sin nueva versión y eventos antiguos borrados que un lector solo del tail podría ignorar.

Los otros seis workflows aplicables del mismo SHA —Premerge, Lab, Book, Brand, Evidence y W01 snapshot— también terminaron en **SUCCESS**; los identificadores originales están en el [checkpoint histórico](../../docs/W01_SOURCE_JOURNAL_CHECKPOINT.es.md). No se creó release.

**Errata del log:** el texto fijo final del workflow imprime **«20/20»** pese a que su aserción y el JSON original validan **22/22**, y las 22 pruebas aparecen individualmente en el log. Es una errata de presentación, no una prueba omitida. El intento posterior de corregir el workflow se bloqueó por controles de seguridad del conector; la evidencia histórica no se ha modificado.

## Límites científicos

El laboratorio usa 16 cuentas y máximo 256 operaciones sintéticas, un solo dominio físico, un escritor administrativo **exclusivo de pruebas**, un journal PostgreSQL creado específicamente y ningún aval independiente del origen bancario. Los hashes no son firmas de procedencia; un operador privilegiado podría reescribir el historial. La auditoría se invoca expresamente, no es una supervisión continua. La consulta reloj-origen/proyección continúa **no linealizable**. No existe prueba de retención CDC, failover real, capacidad bancaria, Golden Master aprobado ni fencing auténtico.

**TODM G2 = `INCONCLUSIVE` y G6 = `BLOCK`**. E2 sigue `partially_verified`; #8 cerrado administrativamente, #32 completado como investigación, #58 **ABIERTO** para validación en cliente y #53 congelado. Este PASS del laboratorio no autoriza producción.
