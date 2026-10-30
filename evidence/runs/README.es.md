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

## Observación E1b ampliada · 30 de octubre de 2026

El [registro original E1b de 7 controles](e1b.json) permanece intacto. Una **ejecución adicional real de GitHub Actions** incorporó tres controles al candidato .NET 10/Npgsql: agotamiento de seis intentos de bloqueo `55P03` sin efectos contables, recuperación e idempotencia al liberar el bloqueo y rechazo por el oráculo SQL independiente de un asiento .NET alterado deliberadamente, que después se restauró.

[Registro ampliado inmutable](e1b-extended.json) · [Ejecución CI #41024101879](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879) · [job y artefacto originales](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879).

**Resultado observado: PASS en los 10 controles.** La primera ejecución de 7 controles conserva su hash de código histórico asociado al commit de 29-10-2026; los hashes del registro ampliado se cotejan con el código actual de la rama. El validador offline **no** confunde el script antiguo con el nuevo. Ninguno de los dos resultados completa todo el contrato SQLite, E1c ni E1 global.

## Paridad directa SQLite ↔ PostgreSQL · 30 de octubre de 2026

El nuevo [JSON inmutable de paridad E1b](e1b-reference-parity.json) conserva la [ejecución CI #41031578923](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41031578923), sus identificadores de job y artefacto, commit, checkout original, hashes, 16 casos individuales y versiones de herramientas. El **ejecutable .NET 10/SQLite de referencia, sin modificar**, y el ejecutable **.NET 10/Npgsql con PostgreSQL** recibieron las mismas operaciones sintéticas. Después de **cada** caso coincidieron saldos, operaciones, asientos y outbox, con un oráculo contable PostgreSQL independiente que pasó los controles.

Se probaron confirmación y rechazo, duplicados y conflictos de identidad, entradas inválidas, excepción y muerte de proceso antes del commit, pérdida de respuesta tras el commit y reintento idempotente. Se liberó un bloqueo real SQLite y otro PostgreSQL mientras los respectivos clientes reintentaban; PostgreSQL registró `55P03` y después confirmó una sola vez. Pasaron los seis grupos de controles y los 16 casos secuenciales.

**No demostrado:** toda la matriz multiproceso SQLite, equivalencia de mecanismos o tiempos de bloqueo, SQL Server, durabilidad ante corte eléctrico, WAN ni capacidad mainframe. Se mantienen intactos los registros E1b anteriores y E1 global sigue parcialmente verificado.

## Tres hallazgos que se pueden comprobar

1. **Deadlock recuperado:** PostgreSQL emitió `40P01`, se reintentó la transacción completa y terminaron dos transferencias confirmadas, sin duplicar asientos.
2. **Aislamiento importa:** el control negativo terminó con 0 operadores activos bajo `READ COMMITTED`; con `SERIALIZABLE` quedó 1 y se observaron dos `40001`.
3. **Un oráculo que contradice:** al eliminar deliberadamente un asiento, el lector independiente detectó el descuadre (`balancedPostings`, `projectionAgrees`, `twoPostingsPerCommit`).

**Reproducción de integridad de la evidencia:**

```bash
python3 scripts/check_e1_observations.py
```

El script comprueba los controles, recalcula los SHA-256 de las observaciones del código vigente y valida el manifiesto histórico fijado de E1b sin confundirlo con el código posterior. El JSON guarda `runId`, `jobId`, commit, límites y resultados. La prueba *no* aporta métricas de capacidad mainframe; el tiempo transcurrido es el de **este ensayo sintético**, no una latencia comercial.

La clasificación global del experimento sigue siendo **E1 parcialmente verificado**: E1c y la paridad completa de contratos permanecen pendientes.
