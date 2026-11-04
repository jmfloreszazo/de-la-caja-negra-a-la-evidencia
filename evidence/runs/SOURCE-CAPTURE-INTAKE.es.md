# Assessment CDC del origen — evidencias estructurales originales y acotadas

**4 de noviembre de 2026.** [English](SOURCE-CAPTURE-INTAKE.md) · [PR #95 fusionado](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/95) · [issue #58 ABIERTO](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58)

## Resultado exacto: metadatos, no CDC nativo

La [ejecución original Source capture owner intake #41898291348](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41898291348), job `126813593665`, terminó SUCCESS con **22/22 pruebas Python estructurales y adversariales**, sin errores inesperados. El ejemplo de assessment produjo el rechazo correcto `NOT_READY`, **7/7 familias UNKNOWN**, `nativeCaptureTestExecuted=false`, `evidenceBytesVerified=false`, `todmG2=INCONCLUSIVE`, `todmG6=BLOCK` y `productionApproved=false`.

- **SHA del código origen del PR**: `e23d5a8dd071655b87e504de2dac255438a534d0`.
- **Checkout realmente ejecutado por GitHub Actions**, que corresponde al *merge temporal de prueba* y no al SHA de origen: `172158b898475d0bf85613ffde8b373e6c9df255`. El log lo identifica como combinación del PR `e23d5a...` con la base `2269d4af09fa4e86da1709bfe35a5d41be410c96`.
- **Commit definitivo en main**, posterior a las pruebas: `18440bd2afc3b62c409fdf93ab2360eb1ba25978`. **No se atribuye una ejecución sobre ese commit a un job del merge temporal.**
- [Extracto literal con timestamps del CI](SOURCE-CAPTURE-PR95-ORIGINAL-CI-EXCERPT.log), guardado en Git: 22 líneas `ok`, resumen `Ran 22 tests` y control de las siete rutas desconocidas. **No es** el log completo ni un ZIP binario.
- Este workflow **no produjo artifact ZIP**. No se afirma checksum independiente de un archivo inexistente, ejecución de un fabricante ni logs nativos del cliente.
- Las referencias IBM del catálogo proceden de extractos indexados por búsqueda; varias páginas devolvieron 403 al intentar abrirlas. La limitación queda registrada sin afirmar que se haya leído un manual íntegro.

## Qué se ha probado y qué sigue sin probarse

Los 22 casos ejercitan familias Db2 z/OS, VSAM CICS, VSAM batch no-RLS, IMS online y DL/I, journals IBM i y Fujitsu/otros por verificar; rutas ausentes y duplicadas; exclusiones sin evidencia de responsable; producto/versión/controles específicos; hashes o URLs incorrectos y falsificaciones de PASS/G2/G6.

Un conjunto de referencias **falsas pero sintácticamente válidas** puede obtener `READY_FOR_INDEPENDENT_REVIEW`; el nombre significa exclusivamente *metadatos listos para verificación independiente*. El programa no lee esos bytes ni consulta bancos, colas MQ, journals, Db2/VSAM/IMS ni productos CDC instalados. Tampoco observa pagos externos, dispensación ATM o rutas privilegiadas de un origen real.

La [campaña anterior W01 PostgreSQL 22/22](W01-SOURCE-JOURNAL.es.md) es un ensayo sintético **diferente**: su PASS financiero acotado no se traslada a la captura nativa del mainframe.

**Clasificación científica:** `STRUCTURAL_INTAKE_TESTS_PASS`; `NATIVE_CAPTURE_NOT_EXECUTED`; `BANK_SOURCE_FENCE_NOT_PROVEN`; `BUSINESS_APPROVAL_NOT_OBTAINED`. TODM **G2 INCONCLUSIVE y G6 BLOCK**. E2 `partially_verified`, #8 cerrado administrativamente, #32 finalizado como método, #58 ABIERTO y #53 congelado. Sin nueva release.

## Próxima demostración real

El responsable debe identificar SO/base de datos/versión instalados y **todas** las rutas de escritura; evaluar online, batch, LOAD/REORG, offline y privilegiados; demostrar el empalme snapshot/log y el replay bajo retención/reinicio; y ejecutar contraejemplos **en logs nativos reales** con permisos controlados. Un revisor independiente debe conciliar apuntes, efectos financieros externos y fencing impuesto por el origen antes de avanzar G2/G6. Consultar el [protocolo de fencing](../../docs/BROWNFIELD_SOURCE_FENCE.es.md).

