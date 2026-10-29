**Español** · [English](../../en/annexes/annex-c-reference-run.md)

[← Anexo B · Contrato del laboratorio](anexo-b-contrato-del-laboratorio.md) · [Índice](../README.md) · [Anexo D · Decisiones de arquitectura →](anexo-d-decisiones-de-arquitectura.md)

# Anexo C · Ejecución de referencia

Ejecución local verificada el 29 de octubre de 2026. El SDK .NET utilizado fue 10.0.403 y el compilador cobc (GnuCOBOL) 3.1.2.0. Los 58 casos completaron la comparación COBOL y C#. Los diez controles de aceptación produjeron los veredictos esperados.

| Control | Veredicto observado | Entrega observada |
|---|---|---|
| none | PASS | SIMULATED_ALLOW |
| round-even | FAIL | BLOCK |
| wrong-threshold | FAIL | BLOCK |
| approve-inactive | FAIL | BLOCK |
| missing-evidence | INCONCLUSIVE | BLOCK |
| missing-case | INCONCLUSIVE | BLOCK |
| duplicate-case | INCONCLUSIVE | BLOCK |
| invalid-anchor | INCONCLUSIVE | BLOCK |
| no-mandate | PASS | BLOCK |
| equal-but-wrong | FAIL | BLOCK |

El módulo transaccional terminó con PASS. Sus controles comprobaron carrera por saldo, duplicados, conflicto de identidad, rollback, caída de proceso, respuesta perdida después de commit, espera de bloqueo, agotamiento de reintentos y rechazo de un historial corrompido deliberadamente. Las seis invariantes de reconciliación fueron verdaderas.

La biblioteca SQLite usada por el proceso C# fue 3.45.1 y la del verificador Python 3.53.1. La diferencia de versión se registra para no atribuir a ambos procesos un entorno idéntico.

Los resultados completos y los hashes de fuentes están en `reference-results/summary.json` y `reference-results/bank/summary.json`, que el laboratorio conserva sin modificar. Las medidas locales no disponen de una baseline mainframe ni de una ejecución en Azure. Su resultado no puede utilizarse para aprobar capacidad empresarial.

Para repetir el proceso, sigue el anexo [A](anexo-a-un-laboratorio-que-pueda-contradecirnos.md): `bash scripts/run-podman.sh --auto` con Podman, o `python3 walkthrough.py --auto --bank` en el entorno nativo descrito. Una ejecución nueva escribe su propio expediente en `results/`.

## Verificación offline

`tools/verify_offline.py` comprueba lo que se puede comprobar sin compiladores. Su resultado: el ancla de la baseline coincide; una tercera implementación de la política en Python reproduce los 58 resultados esperados; todos los fuentes centrales —`fee.cob`, `Candidate`, `Gate`, `Bank`, `run.py`, `bank_test.py` y `cases.json`— son idénticos byte a byte a los registrados en la ejecución de referencia; y el oráculo contable acepta las nueve bases persistidas válidas y rechaza el control negativo por asientos desequilibrados, operaciones sin dos asientos y saldos que no se reconstruyen desde el historial. `walkthrough.py` y `cobol_local.py` solo difieren de la ejecución de referencia en los textos que muestran.

---

[← Anexo B · Contrato del laboratorio](anexo-b-contrato-del-laboratorio.md) · [Índice](../README.md) · [Anexo D · Decisiones de arquitectura →](anexo-d-decisiones-de-arquitectura.md)
