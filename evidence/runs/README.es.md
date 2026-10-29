# Evidencias ejecutadas · E1 PostgreSQL y .NET 10

**Edición experimental**, no resultados de benchmark ni equivalencia con un mainframe. Los JSON que acompañan esta página se extrajeron del bloque de resultados de las ejecuciones **reales** de GitHub Actions. No son capturas reconstruidas ni ejemplos sintéticos del informe.

| Control | E1a · PostgreSQL/Python | E1b · PostgreSQL/.NET 10 |
|---|---|---|
| Procedencia | [CI #40921291469](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40921291469) | [CI #40919773614](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614) |
| Evidencia versionada | [e1a.json](e1a.json) | [e1b.json](e1b.json) |
| Veredicto | PASS, 11 controles | PASS, 7 controles |
| Contención real | `40P01` detectado, transacción reiniciada | Transferencias concurrentes; no se afirma deadlock idéntico |
| Anomalía de aislamiento | `READ COMMITTED`: invariante roto; `SERIALIZABLE`: `40001` y reintento | No cubierto en este subensayo |
| Ledger y outbox | Oráculo SQL independiente, conservación, no negativo, asientos y outbox | Comparación del estado persistido Python/C# + oráculo |
| Control negativo | Borrado intencionado de un asiento detectado | Reutiliza oráculo independiente tras los casos C# |
| Alcance real | Motor PostgreSQL 16.13 en runner Linux/Podman | .NET 10, Npgsql 10.0.3 y PostgreSQL |
| No demostrado | Carga de producción, MIPS, CICS, recuperación distribuida | Paridad de todos los casos SQLite y SQL Server |

## Tres hallazgos que se pueden comprobar

1. **Deadlock recuperado:** PostgreSQL emitió `40P01`, se reintentó la transacción completa y terminaron dos transferencias confirmadas, sin duplicar asientos.
2. **Aislamiento importa:** el control negativo terminó con 0 operadores activos bajo `READ COMMITTED`; con `SERIALIZABLE` quedó 1 y se observaron dos `40001`.
3. **Un oráculo que contradice:** al eliminar deliberadamente un asiento, el lector independiente detectó el descuadre (`balancedPostings`, `projectionAgrees`, `twoPostingsPerCommit`).

**Reproducción de integridad de la evidencia:**

```bash
python3 scripts/check_e1_observations.py
```

El script vuelve a calcular el SHA-256 de los ficheros fuente y comprueba los controles citados. El JSON guarda `runId`, `jobId`, commit, límites y resultados. La prueba *no* aporta métricas de capacidad mainframe; el tiempo transcurrido es el de **este ensayo sintético**, no una latencia comercial.

La clasificación global del experimento sigue siendo **E1 parcialmente verificado**: E1c y la paridad completa de contratos permanecen pendientes.
