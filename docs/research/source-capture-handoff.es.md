# Demostrar la continuidad sintética entre snapshot y journal

**#58 · 4 de noviembre de 2026 · investigación ES.** [English](source-capture-handoff.en.md) · [assessment de CDC por origen](source-native-capture-assessment.es.md) · [evidencia W01 PostgreSQL](../../evidence/runs/W01-SOURCE-JOURNAL.es.md).

## Qué falta después de entrevistar al fabricante

Disponer de documentación de CDC y de un inventario de escritores es **necesario, pero insuficiente**. Una instalación puede tener logs y aun así perder una modificación entre el snapshot inicial y el primer bookmark, consumir eventos duplicados, aceptar datos de otra encarnación del origen o confirmar un destino parcial. Las 22 pruebas del assessment anterior verificaban **metadatos y declaraciones**, no un flujo de cambios real.

El nuevo [oráculo independiente en Python](../../lab/brownfield/source_capture/handoff.py) compara tres elementos sintéticos: saldos justo en el corte, secuencia de COMMIT posteriores y saldos/cursor después del replay. **No interpreta** COBOL, JCL, DDL, logs físicos Db2/IMS, registros VSAM ni formatos propietarios CDC. El catálogo de plataformas solo sirve para etiquetar hipótesis.

## Contrato de la prueba

- Cuatro cuentas sintéticas que parten de 100.000 unidades menores; cinco transferencias confirmadas por el origen de prueba. El snapshot se toma tras la secuencia 2, y el consumidor recibe los eventos 3 a 5.
- Cada transferencia tiene ID único, secuencia y dos efectos contables compensados. Una operación abortada no puede aparecer como confirmada.
- Snapshot y journal deben indicar **la misma encarnación del origen**. La captura debe reanudarse exactamente después del bookmark del corte, y la retención debe conservar la primera modificación necesaria.
- El tail capturado debe coincidir **exactamente** con las transacciones confirmadas del fixture: sin pérdidas, duplicados, desorden, manipulaciones ni operaciones abortadas.
- El cursor del destino y todos los saldos deben concordar con dos reconstrucciones independientes dentro de la prueba. Un corte incompatible, cambio de época, retención expirada, imagen parcial, saldo manipulado o falsa autoaprobación se rechaza.
- Se han preparado 26 tests, incluidos negativos y resultados CLI. Son **pruebas Python offline**: no representan caída real de un mainframe ni lector CDC nativo.

Una traza completamente inventada pero coherente podría superar el oráculo. Para aceptar resultados en un cliente, el historial y el snapshot tienen que provenir del propietario del origen, con autenticidad y versiones comprobadas, un segundo oráculo externo, transacciones y efectos fuera de la base, trazas de todos los escritores online/batch/privilegiados, cobertura de retención y fallos reales. La herramienta **no valida firmas ni descarga pruebas de clientes**.

## Interpretación de los resultados

| Resultado | Qué demuestra |
| --- | --- |
| `PASS_SYNTHETIC_HANDOFF_ORACLE` | Consistencia **solo** del escenario sintético |
| `REJECT` | El corte, secuencia, replay o estado destino no concuerda |
| `INVALID` | Esquema incorrecto, fabricante inexistente o falsa aprobación |

Incluso si el fixture pasa, siempre se informa **TODM G2=INCONCLUSIVE y G6=BLOCK**, `productionApproved=false`, `nativeCaptureTestExecuted=false` y `externalEffectsReconciled=false`.

## Próximos pasos reales para #58

Solicitar al banco una traza original versionada, el bookmark de snapshot certificado por el origen, los COMMIT/UOR consecutivos, política de retención/reinicio, una segunda comprobación independiente y fallos inyectados con el conector nativo que realmente esté instalado. La prueba sintética es un protocolo falsable, **no** aprobación para cortar un core bancario. #53 congelado, E2 `partially_verified`; sin release.

[README y ejecución en inglés](../../lab/brownfield/source_capture/README.md). La [ejecución original #41908404394](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41908404394) ha superado **26/26 controles sintéticos**, con SHA-256 del ZIP original descargado verificado independientemente. Véanse las actas [ES](../../evidence/runs/SOURCE-HANDOFF.es.md) / [EN](../../evidence/runs/SOURCE-HANDOFF.md). **No** supone un PASS de CDC nativo ni del banco.
