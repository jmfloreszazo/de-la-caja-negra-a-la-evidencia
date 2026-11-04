# La captura de cambios del origen es un contrato de plataforma y escritores, no una propiedad de COBOL

**Issue #58 · investigación y assessment del 4 de noviembre de 2026 · sin ejecución nativa de origen.** [English](source-native-capture-assessment.en.md) · [W01 sintético ya probado](../../evidence/runs/W01-SOURCE-JOURNAL.es.md) · [Entrevista y gate ejecutable](../../lab/brownfield/source_capture/README.md).

## Seguimiento: oráculo sintético de continuidad snapshot→tail

La investigación [ES](source-capture-handoff.es.md) / [EN](source-capture-handoff.en.md) incorpora un **oráculo offline con historial sintético independiente**, con 26 controles preparados para corte, bookmark, orden y replay. No constituye captura nativa de fabricante ni modifica la evidencia del assessment anterior o los gates bancarios.

## Decisión

**No debemos trasladar automáticamente el journal PostgreSQL sintético de W01 a un mainframe real.** W01 pasó 22/22 pruebas acotadas entre dos PostgreSQL, con eventos escritos por un *actor de prueba* en el mismo COMMIT financiero. Nunca ha ejecutado un lector nativo de Db2, VSAM, IMS, IBM i ni Fujitsu. El orden de transacciones, la posición de captura inicial, la recuperación, el batch y los efectos externos necesitan evidencias independientes antes de elegir CDC, outbox transaccional aprobado, exportación verificable o conservar el legacy como autoridad.

Incluso cuando CDC replica todas las modificaciones de filas, **eso no demuestra un evento bancario completo**. Dispensar efectivo, enviar pagos a compensación, confirmar al canal, recuperar sucursales offline o efectuar un ajuste de cierre puede atravesar los límites de una UOR de base de datos. Captura de cambios y fencing del escritor original **son controles diferentes**.

## Opciones de captura y fallos que investigar

| Origen real que hay que identificar | Mecanismo documentado *candidato*, no confirmado en cliente | Contraejemplo / prueba necesaria |
| --- | --- | --- |
| **Db2 for z/OS 13** | Un producto de replicación compatible puede leer logs de recuperación; IBM documenta `DATA CAPTURE CHANGES` y Q Capture con entrega mediante MQ | Inventariar tablas, límites LOB/XML, versiones, data sharing, LOAD/REORG, retención, COMMIT, rollback y posición de captura |
| **VSAM bajo CICS** | Classic CDC contempla replication log streams con `IDCAMS LOGREPLICATE` y `LOGSTREAMID` donde corresponda | Contrastar regiones CICS, mappings, RLS/no-RLS, acceso recuperable, cargas masivas y rutas excepcionales |
| **VSAM batch fuera de CICS, no-RLS** | IBM describe captura mediante CICS VSAM Recovery (CICS VR) | Demostrar cobertura JCL batch, apertura directa, utilidades, cargas, checkpoints y restauraciones; el log online de CICS por sí solo no garantiza esas escrituras |
| **IMS online** | Classic CDC puede leer logs online/archivados IMS y syncpoints de la UOR | Verificar tipos IMS soportados, EXIT en DBD, RECON, OLDS/archivos, registros DB/DC/DBCTL y orden multissistema |
| **IMS DL/I batch** | Captura condicional mediante logs de Classic CDC | Comprobar `DBRC=Y`, `DFSFLGX0`, `IEFRDER` permanente y demora hasta cerrar el *job step*, que puede durar horas |
| **IBM i sobre Power** | Journaling de bases de datos y journal receivers, incluidos remotos si están configurados | Identificar archivos físicos journaled, imágenes ANTES/DESPUÉS, continuidad, filtros, eliminación de receivers y commitment control |
| **Fujitsu GS21/BS2000, NEC ACOS, Hitachi VOS, Unisys u otros** | **SIN DETERMINAR en este incremento** | Exigir documentación primaria fechada y versión instalada de SO/base de datos, más prueba de recuperación nativa; no trasladar terminología IBM por analogía |

**Referencias oficiales consultadas (no equivalen a instalar o ejecutar el producto):**

- IBM [Db2 for z/OS 13 y límites de captura](https://www.ibm.com/docs/en/db2-for-zos/13.0.0?topic=tables-altering-table-capture-changed-data); [Q Capture / Q Apply](https://www.ibm.com/docs/en/idr/11.4.0?topic=zos-replication-event-publishing-programs).
- IBM [preguntas VSAM y diferencias de escritores](https://www.ibm.com/docs/en/idr/11.4.0?topic=zos-frequently-asked-questions); [LOGREPLICATE y LOGSTREAMID](https://www.ibm.com/docs/en/idr/11.4.0?topic=replication-augmenting-vsam-data-sets-change-data-capture).
- IBM [requisitos y restricciones IMS DL/I](https://www.ibm.com/docs/en/idr/11.4.0?topic=architect-system-requirements-ims); [logs IMS y latencia](https://www.ibm.com/docs/en/idr/11.4.0?topic=processing-reading-ims-logs); [EXIT de captura DBD](https://www.ibm.com/docs/en/idr/11.4.0?topic=information-augmenting-downloading-dbds-ims-change-data-capture).
- IBM [journal receivers de IBM i](https://www.ibm.com/docs/en/i/7.6.0?topic=database-journal-management-distributed-relational-databases); [remotos y filtros](https://www.ibm.com/docs/en/i/7.5.0?topic=concepts-journal-receivers-associated-remote-journal).

Estas referencias tienen **ámbito de versión de documentación**, no prueban la configuración, licencias, soporte ni disponibilidad del cliente en 2026. No afirmamos ningún CDC nativo concreto de Fujitsu: quedan pendientes fuentes primarias específicas y firmadas. La compatibilidad y el fin de soporte deben contrastarse con fabricante/cliente.

## Entrevista y observaciones reproducibles

El [catálogo estructurado](../../lab/brownfield/source_capture/capture_catalog.json) distingue referencias y lagunas; el [intake ejemplo](../../lab/brownfield/source_capture/intake.example.json) deja las **siete familias en UNKNOWN**, sin aprobar nada. Deben participar responsable funcional, DBA, administrador CICS/IMS, batch, almacenamiento/log/DR, seguridad, canal/pagos y conciliación independiente.

Para cada ruta aplicable:

1. **Unidad de COMMIT y watermark de origen:** ¿quién asigna la posición y a qué nivel — subsistema, dataset, receptor de journal, cola o clave? Un timestamp no es automáticamente un orden global de transacciones.
2. **Empalme snapshot ↔ log:** ¿qué protocolo garantiza que el corte inicial y los COMMIT posteriores no dejan huecos ni duplicados?
3. **Reinicio y retención:** bookmarks, vencimiento de archivos/receivers, batch DL/I, offline, rollback, recaptura, cambios de esquema e inyección deliberada de una pérdida de segmento. No saltar silenciosamente al último evento.
4. **Cobertura de escritores:** CICS/IMS, JCL, LOAD/REORG, ATM/canales, sucursales desconectadas, reintentos asíncronos y operadores privilegiados. Un conector CDC puede cubrir **menos rutas que las que producen consecuencias financieras**.
5. **Conciliación independiente:** comparar IDs, apuntes pareados, invariantes, versiones y efectos externos de pagos/efectivo, además de estados `UNKNOWN`, no únicamente cantidades de filas.
6. **Seguridad y autoridad:** fencing impuesto por el legacy y prueba de corte/retroceso controlado ante fallos; capturar datos no convierte automáticamente al nuevo sistema en escritor autorizado.

**Decisiones:** `RETAIN_SOURCE`, `CONDITIONALLY_DESIGN`, `INCONCLUSIVE` o `READY_FOR_EXTERNAL_REVIEW`. No existe decisión automática `MOVE_LEDGER` ni un PASS bancario. Si no hay log completo o accesible, podría tener valor una sombra de lectura/exportación **aprobada y conciliada**, pero no debemos prometer frescura casi inmediata ni permitir efectos financieros nuevos.

## Alcance del incremento y estado científico

El nuevo gate ejecuta exclusivamente **pruebas estructurales de un formulario y rechazos adversariales**. Un conjunto de referencias falsas, pero sintácticamente completo, puede producir `READY_FOR_INDEPENDENT_REVIEW`; el propio reporte conserva `evidenceBytesVerified=false` y `nativeCaptureTestExecuted=false`. Sus pruebas unitarias **no** ejecutan plataformas IBM o Fujitsu ni verifican evidencias de cliente. La demostración real de W01 sigue siendo únicamente la campaña PostgreSQL sintética de 22 casos.

El [protocolo de fencing](../BROWNFIELD_SOURCE_FENCE.es.md) y el [issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58) continúan abiertos para aceptación independiente. **TODM G2 `INCONCLUSIVE`, G6 `BLOCK`**. E2 conserva `partially_verified`; #8 cerrado administrativamente, #32 cerrado como metodología y #53 congelado. No se autoriza ninguna release.
