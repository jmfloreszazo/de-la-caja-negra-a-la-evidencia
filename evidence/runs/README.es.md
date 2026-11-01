# Evidencias ejecutadas · E1 PostgreSQL y .NET 10

**Evidencia original C2:** [procedencia y límites en español](BROWNFIELD-JOURNAL.es.md) · [observaciones extraídas del log](brownfield-c2-pr66-ci-log-extracted.json). Ensayo sintético parcial; los negativos de UNKNOWN/bypass son intencionados, G6=BLOCK.

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

## SQL Server E1c: resultado completo de la matriz sintética · 30 de octubre de 2026

[Ejecución CI original #41042317263](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) · [registro original legible por máquina](e1c-sqlserver-worker-parity.json). La referencia intacta .NET 10/SQLite y el candidato independiente .NET 10/SQL Server 2022 Developer ejecutaron ocho escenarios sintéticos uniformes y de cuenta caliente con **1, 2, 4 y 8 trabajadores, 32 comandos por trabajador**. En los ocho escenarios, **cada candidato confirmó 960 transferencias**, coincidieron las cuatro tablas persistidas y pasaron los siete invariantes contables independientes. Se conservan identificadores de ejecución, job y artefacto, commits de origen y checkout temporal, hashes y veredictos individuales.

Las evidencias anteriores [E1c de ocho controles](e1c-sqlserver-initial.json) y [E1c ampliada a diez](e1c-sqlserver-extended.json) demuestran de forma independiente reintentos tras deadlock real `1205`, seis bloqueos `1222` acotados, control negativo de *write skew* con `SNAPSHOT`, protección con `SERIALIZABLE`, rechazo de corrupción contable, clave única y timeout separado del cliente `-2`. Las filas E1a/E1b de la tabla inicial representan exclusivamente **sus primeras ejecuciones históricas**.

**Límite:** los trabajadores SQLite permanecen vivos, mientras SQL Server inicia un proceso .NET por transferencia. Se acredita paridad funcional y contable en esa matriz concreta, **no** throughput, latencia, durabilidad ante corte eléctrico, HA de SQL Server, producción bancaria ni equivalencia MIPS. E1 global continúa parcialmente verificado y la PR no está fusionada.

## Observación E1b ampliada · 30 de octubre de 2026

El [registro original E1b de 7 controles](e1b.json) permanece intacto. Una **ejecución adicional real de GitHub Actions** incorporó tres controles al candidato .NET 10/Npgsql: agotamiento de seis intentos de bloqueo `55P03` sin efectos contables, recuperación e idempotencia al liberar el bloqueo y rechazo por el oráculo SQL independiente de un asiento .NET alterado deliberadamente, que después se restauró.

[Registro ampliado inmutable](e1b-extended.json) · [Ejecución CI #41024101879](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879) · [job y artefacto originales](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879).

**Resultado observado: PASS en los 10 controles.** La primera ejecución de 7 controles conserva su hash de código histórico asociado al commit de 29-10-2026; los hashes del registro ampliado se cotejan con el código actual de la rama. El validador offline **no** confunde el script antiguo con el nuevo. Ninguno de los dos resultados completa todo el contrato SQLite, E1c ni E1 global.

## Paridad directa SQLite ↔ PostgreSQL · 30 de octubre de 2026

El nuevo [JSON inmutable de paridad E1b](e1b-reference-parity.json) conserva la [ejecución CI #41031578923](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41031578923), sus identificadores de job y artefacto, commit, checkout original, hashes, 16 casos individuales y versiones de herramientas. El **ejecutable .NET 10/SQLite de referencia, sin modificar**, y el ejecutable **.NET 10/Npgsql con PostgreSQL** recibieron las mismas operaciones sintéticas. Después de **cada** caso coincidieron saldos, operaciones, asientos y outbox, con un oráculo contable PostgreSQL independiente que pasó los controles.

Se probaron confirmación y rechazo, duplicados y conflictos de identidad, entradas inválidas, excepción y muerte de proceso antes del commit, pérdida de respuesta tras el commit y reintento idempotente. Se liberó un bloqueo real SQLite y otro PostgreSQL mientras los respectivos clientes reintentaban; PostgreSQL registró `55P03` y después confirmó una sola vez. Pasaron los seis grupos de controles y los 16 casos secuenciales.

**No demostrado:** toda la matriz multiproceso SQLite, equivalencia de mecanismos o tiempos de bloqueo, SQL Server, durabilidad ante corte eléctrico, WAN ni capacidad mainframe. Se mantienen intactos los registros E1b anteriores y E1 global sigue parcialmente verificado.

## Vectores completos del oráculo independiente · 30 de octubre de 2026

[Ejecución original #41032714628](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41032714628) · [Vectores antes/corrupto/restaurado](e1b-oracle-vectors.json). El oráculo PostgreSQL independiente y de solo lectura evaluó siete invariantes tras la prueba directa entre motores. Los siete pasaron inicialmente. Al eliminar un asiento realmente confirmado se detectaron exactamente **tres fallos**: `balancedPostings`, `twoPostingsPerCommit` y `projectionAgrees`. La restauración de la misma fila devolvió los siete a PASS. Se conservan la ejecución, el manifiesto y el artefacto CI originales.

Es un **control negativo sintético en una sola base de datos**, no una simulación de fallos productivos ni una demostración de capacidad mainframe. Los hashes del código se comprueban sin reescribir las observaciones históricas. E1 global continúa parcialmente verificado.

## Manifiesto de reproducibilidad · 30 de octubre de 2026

[Manifiesto versionado](e1b-runtime-manifest.json) · [ejecución CI #41033595770](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41033595770). La evidencia conserva las versiones de Python, .NET SDK, Npgsql, psycopg, SQLite nativo, PostgreSQL y Podman; el identificador y digests SHA-256 de la imagen PostgreSQL; seis hashes de código; y por separado el **HEAD original de la PR** y el **checkout temporal de merge** de GitHub. La CI verifica el job de procedencia. Estos datos permiten reproducir mejor el ensayo, pero no prueban portabilidad multiplataforma ni equivalencia operativa.

## Paridad de la matriz multiproceso · 30 de octubre de 2026

[Ejecución original de 960 transferencias](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41034420329) · [resultado legible por máquina](e1b-multiprocess-parity.json). Pasaron los **ocho** casos sintéticos: distribución uniforme y cuenta caliente, con 1, 2, 4 y 8 trabajadores de referencia SQLite y **32 operaciones por trabajador**. El candidato PostgreSQL/.NET 10 reprodujo concurrentemente los mismos identificadores, cuentas e importes. En cada escenario coincidieron saldos, operaciones, asientos y outbox; además, pasaron los siete invariantes contables independientes. Ambos candidatos confirmaron las **960 transferencias lógicas**.

La referencia SQLite utilizó sus **procesos trabajadores persistentes**, mientras que PostgreSQL inició un proceso .NET por transferencia. Por tanto, tiempos, sobrecarga de lanzamiento, reintentos y tasas de operaciones **no son comparaciones de rendimiento válidas**. Queda contrastado el contrato contable sintético de la matriz uniforme/caliente; SQL Server y la capacidad operativa mainframe continúan fuera de E1b.

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
