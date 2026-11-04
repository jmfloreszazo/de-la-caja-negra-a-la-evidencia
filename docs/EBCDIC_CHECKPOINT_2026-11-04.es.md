# EBCDIC/CCSID: corte de evidencia acotada

PR #88 entrega la kata de #11: 36 comprobaciones y cuatro transformaciones erróneas rechazadas en cada uno de tres sistemas operativos. La ejecución original [41801198131](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41801198131), fuente y checkout `3783f94249b3d3e3efd36096ec029b795eda2648`, pasó los tres jobs a la primera. Los ZIP se conservan sin modificar; no se inventan fallos anteriores.

| Runner | Python | Artifact | ZIP SHA-256 |
| --- | --- | --- | --- |
| ubuntu-24.04 | 3.12.15 | [13306629254](../evidence/editorial/ebcdic-original-ubuntu-24.04.zip) | `3b4e99e9909f3f0078fd957cfeabe2f4c0a190b644d4467a0a8cba032aa0839f` |
| macos-14 | 3.12.10 | [13307842169](../evidence/editorial/ebcdic-original-macos-14.zip) | `efb71552f14c7bdfa12d460a401b8026b247f86f955d1923c3d90cb579b8a362` |
| windows-2022 | 3.12.10 | [13307238043](../evidence/editorial/ebcdic-original-windows-2022.zip) | `474e11633fe7652d66157306c1ea28607441cb34805f6fd449fa0d2462220e0a` |

El [manifiesto](../evidence/editorial/ebcdic-original-manifest.json) conserva tamaño, identidad y plataforma real. `python3 scripts/check_ebcdic_observations.py` comprueba los ZIP, identidades, inventario de 36 casos, valores documentados, registros esperados, cuatro resultados alterados y tres hashes históricos por job. Un checkout superficial debe descargar primero la fuente original.

En Windows, los tres archivos fuente observados tienen CRLF y rutas con barra inversa; sus hashes difieren de los blobs Git con LF. La auditoría verifica exactamente la transformación LF→CRLF para ese job y normaliza solo el separador del nombre al consultar Git. No reescribe los originales ni presenta sus hashes como idénticos.

El capítulo 12 y las fuentes [63]/[64] están en ambos idiomas. El [README de la kata](../lab/examples/ebcdic-boundaries/README.md) fija autoridad sintética, protocolo, ejecución y limitaciones. Los catorce valores documentados son una autoridad separada de los codecs; las vueltas de los 256 bytes solo comprueban autoconsistencia. Los cuatro mutantes son transformaciones de resultados que califican predicados concretos, no pruebas de todo conversor posible.

Esto cumple el subpaso acotado de kata EBCDIC/CCSID. #11 sigue abierto para los demás listados, revisión editorial integral y reproducción del laboratorio completo en macOS/Podman machine y Windows/WSL2. No se ha ejecutado conversión nativa de z/OS, Db2 o MQ; faltan registros reales autorizados, framing de datasets, DBCS y el trayecto host/transferencia/destino. La guía describe cómo validarlos sin bloquear este incremento. No cambia etiquetas de listados, fuentes financieras protegidas, aprobación bancaria ni release.
