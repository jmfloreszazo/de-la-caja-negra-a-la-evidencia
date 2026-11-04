# Contratos de ejecución por fabricante — campaña original acotada

[English](VENDOR-RUNTIME-CONTRACTS.md) · [PR #97](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/97) · [Catálogo de fuentes](../../research/vendor-runtime-contracts/catalog.json) · [Investigación ES](../../docs/research/vendor-runtime-contracts.es.md)

**Evidencia recogida: 4 de noviembre de 2026. Se valida METADATO, nunca una plataforma real del fabricante.**

## Evidencia original realmente ejecutada

- [GitHub Actions original #41914291930](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41914291930), job `126869737831`, SHA original de fuente y checkout `7dde2c7cff508206c2f154a4e55de798d4cff78c`.
- **25/25 pruebas de integridad superadas**, una base y 24 mutaciones negativas, sin fallos inesperados. El corpus original contiene **10 referencias de fabricantes fechadas y 11 contratos o entradas de descubrimiento**. El [extracto literal de las 25 pruebas](VENDOR-RUNTIME-PR97-ORIGINAL-CI-EXCERPT.log) conserva las marcas temporales del job.
- GitHub publicó el artifact `13365075026`, `vendor-runtime-contract-metadata-original-not-native`, 1847 bytes, digest ZIP informado por GitHub `sha256:fb3ec79701bfc325fdf93e597b777f44dad5003e66f72c26be409c2d0e54c987`, caducidad inicial 2 de febrero de 2027. **No se han descargado y recalculado de manera independiente los bytes del ZIP**: el digest se refiere a metadatos de GitHub. [Resumen estructurado de ejecución](vendor-runtime-pr97-original-ci-summary.json).
- **Fallo histórico conservado:** [run #41914127029](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41914127029) falló porque un *test adversarial estaba mal preparado*: relacionaba una fila OS 2200 con una fuente MCP de Unisys y esperaba un error entre fabricantes, cuando ambos eran del mismo fabricante. Se corrigió el test para cruzar realmente IBM y Unisys y se repitió. El primer run mantiene **FAIL**, sin reetiquetarlo como PASS.

## Alcance exacto

La suite rechaza fuentes sin fabricante o versión, anuncios históricos elevados a garantías técnicas, fallos/oráculos ausentes, fechas inexistentes, desconocidos transformados en «no soportado» y afirmaciones falsas de ejecución nativa, equivalencia, SLO o aprobación bancaria. El resultado original es `PASS_METADATA_INTEGRITY_25_CASES`, `nativeExecution=false`, `parityVerified=false`, `productionApproved=false`; TODM **G2 INCONCLUSIVE / G6 BLOCK**.

Esto **no** significa que hayamos ejecutado IBM Z/z/OS, Db2 z/OS, IBM i, MCP, OS 2200, Fujitsu GS21, NEC o Bull GCOS. No se ha usado código real de clientes, leído logs nativos, certificado ninguna versión instalada, demostrado paridad operativa ni medido equivalencias MIPS/vCPU, latencia, RPO o RTO. Las páginas IBM se recuperaron por índice, pero el acceso directo dio HTTP 403. Algunas páginas Unisys se leyeron íntegramente y la referencia Fujitsu es **un anuncio histórico de 2018**. Estos límites permanecen en el catálogo.

Los capítulos 1 y 13 ampliados, el manuscrito bilingüe y las versiones monolíticas generadas son resultados editoriales, no evidencia del mainframe. Los issues #17/#18/#28 continúan abiertos para completar la cobertura, el #58 para fencing del sistema real y #53 permanece congelado. Sin nueva release ni aprobación de cutover.
