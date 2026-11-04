# W01 CAP-005 — ejecución original de proyección/fallback PostgreSQL (4 de noviembre de 2026)

[English](W01-PROJECTION.md) · [Diseño W01 y límites](../../docs/research/w01-projection.es.md) · [PR #92 fusionado](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/92)

## Afirmación acotada realmente verificada

**`PASS_BOUNDED_SYNTHETIC_TESTS` — 16 pruebas sobre PostgreSQL real superadas en un checkout del SHA exacto del PR.** No significa un PASS global de la migración ni una aceptación bancaria.

- **Ejecución original:** [GitHub Actions W01 #41853096276](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853096276); job `126654375641`.
- **SHA exacto de fuente y checkout:** `730b40a241986fbd4975d60285bd1b149ec743f3`, coincidentes en el JSON original.
- **Commit de fusión:** `ce96fa0f4c8f4be950f08b67d8ae8e6049878e20`. No se atribuye la ejecución del PR al checkout de `main` ya fusionado.
- **Artifact original de Actions:** ID `13334909404`, nombre `w01-postgresql-synthetic-original-not-bank-approved`, **2462 bytes**. GitHub publica en sus metadatos el digest ZIP `sha256:c467243029ca0f37d0683c59f1b5fd242a01874eb73182ca475beecf5c8ad2ca`, con fecha inicial de expiración 2 de febrero de 2027. **No** se afirma que este commit haya descargado los bytes para recalcular el SHA de forma independiente.
- **Conservación permanente en Git:** [extracto literal del log original de CI](W01-PR92-ORIGINAL-CI-EXCERPT.log) con los 16 tests y gate de evidencia; [JSON transcrito del log y metadatos del artifact original](w01-pr92-original-ci-summary.json). El extracto **no es el log completo**, y el JSON transcrito **no es el ZIP binario original**.
- **Infraestructura:** dos clústeres reales PostgreSQL 16.13 con identificadores de sistema distintos, cada uno en Podman, pero en **un único runner físico alojado Ubuntu 24.04**. Dos identificadores no demuestran dominios físicos independientes.
- **Entorno:** el resultado original registra Python 3.12.15. El artifact de Actions incluye los logs completos, identidad de imagen PostgreSQL y demás procedencia.

## Controles ejecutados y superados

| Grupo | Casos originales PASS |
| --- | --- |
| Inicio y contabilidad | 01 fallback sin proyección; 02 primera reconstrucción, origen read-only y oráculo SQL independiente; 16 consultas repetidas sin alterar tablas financieras del origen |
| COMMIT real y frescura | 03 transferencia confirmada en origen deja la proyección obsoleta y activa fallback; 04 reconstrucción y replay idempotente; 05 mínimo de versión atendido por origen; 06 mínimo inalcanzable bloqueado |
| Corrupción y regresión | 07 corrupción detectada, fallback y reparación explícita; 08 modificación del origen sin avanzar reloj rechazada **al refrescar**; 09 regresión de watermark rechazada |
| Fallos y disponibilidad | 10 proyección inaccesible → origen; 11 reloj de origen inaccesible → BLOCK; 12 falla el fallback → BLOCK |
| Guardas y topología | 13 parámetros inválidos rechazados; 14 endpoint no-loopback u opt-in ausente rechazado; 15 identidad diferente de clúster PostgreSQL |

**16/16 casos PASS y cero FAIL/ERROR inesperados.** Los casos adversariales cuentan como pruebas superadas precisamente porque la implementación **rechaza** la condición peligrosa. No se afirma que un incidente productivo haya quedado solventado.

El oráculo independiente inspecciona PostgreSQL y verifica conservación de saldos, dos apuntes compensados por operación admitida, un outbox, secuencia de origen y revisiones. La aplicación de proyección solo consulta el origen en **transacciones de solo lectura** y escribe exclusivamente en la base de proyección. El escritor financiero de las pruebas es **otro actor sintético** y confirma saldo, apuntes, outbox y reloj en una única transacción.

## Límite científico que no debemos ocultar

La consulta primero observa el reloj del origen y después accede a la proyección. Una transacción puede confirmar **justo después** de leer ese reloj. Por tanto `PROJECTION_OBSERVED_CURRENT` significa vigente respecto de **la muestra observada**, no un saldo linealizable y autoritativo. Si un escritor privilegiado modifica saldos del origen sin incrementar la secuencia, **una consulta basada solo en watermark no detecta el bypass en ese momento**; el siguiente refresco se niega al encontrar datos diferentes con el mismo reloj.

Para usarlo en un banco faltan: disciplina de versión impuesta por todos los escritores reales, contrato de CDC o frontera de snapshot/reconstrucción, detección de gaps, autorización, presupuesto de retraso, recuperación, consistencia por canal y oráculos aprobados.

No se ha probado CDC continuo, HA física, mejora productiva de TPS/p99, autorización ATM, integración real con mainframe, fencing del origen propiedad del banco, Golden Master aprobado ni SLO operacionales. **TODM G2 = INCONCLUSIVE y G6 = BLOCK.** Las 30 capacidades siguen siendo hipótesis; #32 y #58 continúan abiertos; E2 #8 sigue cerrado y #53 congelado. No autoriza release ni versión nueva.

## Workflows complementarios

Sobre el mismo SHA del PR se ejecutaron correctamente [Premerge #41853095794](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853095794), [Lab #41853095727](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853095727) (offline, nativo y Podman), y [Functional extraction waves #41853096032](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853096032). En [Book #41853096066](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853096066) finalizó con **SUCCESS completo** en el SHA original del PR: Markdown, enlaces/sincronización ES/EN y diagramas pasaron (verificado tras el primer corte). Este PR no cambió fuentes de figuras ni capítulos generados.
