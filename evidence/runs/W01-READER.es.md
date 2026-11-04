# W01 con lector restringido — evidencias PostgreSQL originales (4 de noviembre de 2026)

[English](W01-READER.md) · [Acta original W01 de 16 pruebas](W01-PROJECTION.es.md) · [PR #93 fusionado](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/93)

## Resultado acotado demostrado

**`PASS_BOUNDED_SYNTHETIC_TESTS`: 20/20 pruebas sobre PostgreSQL 16.13 real, con dos clústeres de bases de datos en UN SOLO runner GitHub.** Se añaden cuatro casos a la campaña anterior sin reescribir la evidencia histórica de 16 pruebas ni cambiar su SHA.

- [GitHub Actions W01 lector restringido #41855993179](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41855993179), job `126664633712`.
- SHA original de fuente y checkout `fc248c0ba72f40ac797b407dac818d2e1ad7219e`; commit de fusión `0894478ddbc2733e1fcffbd44c4b5b1137ed06db`.
- Artifact publicado por GitHub: ID `13336738360`, nombre `w01-postgresql-synthetic-original-not-bank-approved`, 2.838 bytes, digest ZIP `sha256:8a8b036c2ac47d73a4a065e73bf1b7484a41be0fa39a77b71f37d75c25b1831f`; caduca inicialmente el 2 de febrero de 2027. Ese checksum procede de los **metadatos de GitHub**; el acta no afirma haber descargado y recalculado el ZIP binario.
- [Extracto literal de líneas del CI original](W01-READER-PR93-ORIGINAL-CI-EXCERPT.log) y [JSON transcrito de su salida con metadatos del artifact](w01-reader-pr93-original-ci-summary.json). Estas copias **no son** el log completo ni el archivo ZIP original.

## Controles negativos ejecutados

| Caso | Evidencia observada |
| --- | --- |
| Denegación SQL | PostgreSQL rechaza el UPDATE del lector `w01_reader` sobre `legacy.accounts` con `42501 InsufficientPrivilege`, incluso tras `SET TRANSACTION READ WRITE`; también rechaza modificar el reloj y consultar el historial financiero no permitido |
| Rechazo de superusuario | El proyector no acepta `postgres` como identidad de origen; comprueba rol efectivo y permisos SQL reales, no únicamente una cadena DSN |
| CLI aislada | Una ejecución en proceso separado recibe solo la DSN `w01_reader`, sin DSN administrativa en sus variables de entorno; responde con fallback no autorizado para gastar |
| Resets desechables | Los dos destinos administrativos exactos se verifican **antes** de borrar cualquiera de sus esquemas; se rechazan endpoints remotos y el origen permanece intacto |
| Regresión funcional | Se conservan los 16 casos anteriores de watermark, fallback, corrupción, mutación privilegiada detectada **al refrescar**, regresión de reloj, fallos, oráculo contable e identidad de clúster |

**Alcance preciso:** los permisos de PostgreSQL impiden que **la identidad lectora** escriba en las tablas financieras del fixture. El **proceso de pruebas** todavía posee credenciales de superusuario para preparar datos y simular transferencias; no se ha demostrado aislamiento de secretos en producción.

## Límites aún pendientes

No existe demostración de identidad ni fencing en COBOL/CICS/IMS/Db2 reales, protección contra un escritor privilegiado del banco, obligatoriedad del reloj, saldo linealizable, CDC, HA física, carga productiva ni Golden Master/política de negocio aprobados. Una lectura por watermark puede omitir una modificación del origen sin nueva versión y un COMMIT posterior a muestrear el reloj; véase el [acta W01 original](W01-PROJECTION.es.md). Estas pruebas **no constituyen aceptación bancaria**.

**TODM G2 `INCONCLUSIVE` / G6 `BLOCK`**; #32 y #58 continúan abiertos, E2 #8 cerrado administrativamente y #53 congelado. No se autoriza despliegue ni release. Ver la guía [ES](../../docs/research/w01-reader-identity.es.md) y [EN](../../docs/research/w01-reader-identity.en.md).

## Workflows adicionales

Premerge, Brand artwork, Lab (offline/nativo/Podman) y W01 están en PASS sobre el mismo SHA original. [Book #41855993301](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41855993301) **finalizó con SUCCESS completo** en el SHA exacto del PR: diagramas, Markdown, enlaces y sincronización ES/EN superados. Comprobado después de la observación inicial parcial. No se han cambiado fuentes de figuras.
