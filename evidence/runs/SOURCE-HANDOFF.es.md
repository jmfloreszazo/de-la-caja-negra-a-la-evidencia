# Continuidad snapshot/journal — ejecución original de 26 controles sintéticos

**4 de noviembre de 2026 · issue #58 · PR #96.** [English](SOURCE-HANDOFF.md) · [protocolo de investigación](../../docs/research/source-capture-handoff.es.md) · [Actions original](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41908404394).

## Resultado técnico auditado

**PASS_BOUNDED_SYNTHETIC_HANDOFF: 26/26 pruebas Python positivas y negativas superadas, cero fallos inesperados y cero pruebas omitidas.** SHA original de código y checkout: `63c2e2119d662569b92bb99791a4eb4d471355e4`. Job original `126849132395` en [Actions #41908404394](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41908404394).

**ZIP de GitHub Actions descargado y auditado:** artifact `source-capture-handoff-synthetic-only-original`, ID `13360258324`, **2099 bytes**. SHA-256 recalculado de los bytes originales:
`b15bf9d394d53f93280e707c9df538420ea22f53eeeb6d0a3c87b77aad0e943c`,
**idéntico** al digest publicado por GitHub. CRC correcto en los tres archivos: `original-result.json`, `test-original.log` y `provenance.txt`. Entorno original Python 3.12.15 y runner Ubuntu Linux x86_64. Caducidad inicial del artifact: 2 de febrero de 2027.

El JSON original informa `testsRun=testsPlanned=26`, `unexpectedFailures=0`, `skipped=0`, `nativeSourceCaptureExecuted=false`, `customerEvidenceBytesChecked=false`, `externalEffectOracle=false`, `realSourceWriterFence=false` y `productionApproved=false`. El [registro estructurado](source-handoff-pr96-audited-original.json) conserva metadatos y hashes de código informados por el runner; el [extracto literal del log](SOURCE-HANDOFF-PR96-ORIGINAL-CI-EXCERPT.log) conserva las 26 pruebas nombradas. Es **un extracto**, no el ZIP original íntegro.

## Qué se ha demostrado exactamente

El **origen es un fixture sintético**, no un mainframe. La suite compara un historial de COMMIT declarado independientemente con saldos del snapshot, cursor de continuación, retención, identidad y orden del tail, operación abortada, encarnación del origen y saldos finales. Rechaza secuencias ausentes, duplicadas o desordenadas, imágenes cambiadas, cursor incorrecto, entrada inválida y falsas autoaprobaciones. El ejemplo tiene cuatro cuentas, cinco transferencias ficticias, corte en secuencia 2 y captura 3–5.

**No** demuestra autenticidad del historial, orden real de UOR/Db2, cobertura CICS/VSAM/IMS batch, receivers IBM i, características Fujitsu, failover físico, pagos/efectos externos, fencing del banco, rendimiento productivo ni Golden Master aprobado. Un historial de origen **inventado pero internamente coherente** podría superar el oráculo. La evidencia real deberá proceder de un origen bancario autenticado y de un segundo oráculo independiente.

**Sin aprobación de negocio:** TODM **G2 = INCONCLUSIVE / G6 = BLOCK**. E2 sigue `partially_verified`, #58 continúa ABIERTO; #32 terminado como investigación y #53 congelado. Ninguna release ni corte de producción se autoriza con este resultado.

Esta acta corresponde al **SHA original del PR** y no afirma haber reejecutado las pruebas sobre un commit posterior de documentación o fusión.