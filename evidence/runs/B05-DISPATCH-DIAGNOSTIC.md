# B05: direct admission-slot diagnostic / diagnóstico de admisión directa

## English

This is a bounded client-admission observation under issue #25, not a capacity ceiling. [Original run 41656639275](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41656639275) executed source `97e2efcf399c9ef75b4b093c22e36cfb5622cb17`. All three original cohort jobs succeeded. The three byte-identical original ZIPs and compact recomputed [audit](b05-dispatch-41656639275/audit.json) are preserved in [the campaign directory](b05-dispatch-41656639275/).

Each cohort ran a fresh native direct client against a fresh SQL fixture for each admission limit. PostgreSQL 16.13 ran as a Docker service on the same GitHub runner, with fsync, synchronous_commit and transaction commit timestamps enabled. Npgsql's pool remained fixed at 32. Cohorts 0/2 used limits 32 then 128; cohort 1 reversed the order. All six trials used the exact same 19,840-offer vector: 320 offered/s, 1s warmup, 60s measurement, 1s cooldown, 1,000 accounts and exactly 80% of source intents from 50 hot accounts. These are three runner cohorts, not independent physical availability domains.

| Cohort | Admission limit | Warmup misses | Measurement misses | Total SQL commits | Certain SQL commits/s in 60s window |
|---|---:|---:|---:|---:|---:|
| 0 | 32 | 16 | 24 | 19,800 | 319.6000 |
| 0 | 128 | 0 | 0 | 19,840 | 320.0000 |
| 1 | 128 | 0 | 0 | 19,840 | 320.0167 |
| 1 | 32 | 55 | 0 | 19,785 | 320.0167 |
| 2 | 32 | 58 | 0 | 19,782 | 320.0167 |
| 2 | 128 | 0 | 0 | 19,840 | 320.0167 |

Across 119,040 offers, 118,887 were committed and acknowledged, 153 hit the admission limit and none had an ambiguous exception. Every miss occurred with exactly 32 active slots. Independent reconstruction of persisted operations, paired postings, balances and outbox passed all seven invariants in each trial (42 checks). SQL throughput uses server commit timestamps in a conservative clock interval, not ACK counts; phase boundaries can include a commit from an adjacent offer phase, explaining 320.0167/s without exceeding the fixed offered contract. Measurement-phase offer outcomes and SQL-clock intervals are separate quantities.

With limit 128, warmup peaks were 51, 93 and 92 active slots; measurement peaks were 26, 17 and 6. With limit 32, measurement peaks were 32, 6 and 10. The larger cap admitted every offer in these six paired observations. This supports an admission-policy effect in this setup; the order reversal does not eliminate runner noise, and it does not locate a backend saturation point. It also does not establish the cause of the historical 12 warmup misses: that older client did not retain exact decision/release events.

All-offer decision lag and completion-to-release delay are retained by phase, alongside CPU, working-set, GC and PostgreSQL wait observations. Latency of admitted survivors alone is not service p99. Exact pool-acquisition waits are not instrumented, so a 32-connection pool must not be called the bottleneck from these observations. No Orleans routing, silo scaling, natural grain lifecycle, physical HA, production throughput, MIPS or TCO result is claimed. Instrumentation itself changes timing; this topology differs from the older two-silo Podman campaign.

Reproduce the frozen audit with `python3 scripts/check_b05_dispatch.py`; it verifies the three original ZIP digests, original source hashes, full offer vector, exact slot traces and independent SQL states. The source workflow compiles and checks contracts on PRs; new live campaigns require its manual dispatch. The archive workflow recomputes the frozen originals. A skipped live matrix is not an executed PASS. No experimental acceptance criterion was relaxed.

## Español

Es una observación acotada de admisión del cliente dentro de #25; no establece un techo de capacidad. La ejecución original y su commit quedan identificados arriba, junto con los tres ZIP originales sin modificar y su auditoría reproducible. Las tres cohortes terminaron correctamente.

Cada cohorte utilizó un proceso cliente directo nuevo y reinició los datos SQL para cada límite. PostgreSQL 16.13 se ejecutó en Docker dentro del mismo runner de GitHub, con fsync, synchronous_commit y marcas de commit activados. El pool de Npgsql permaneció en 32 conexiones. Las cohortes 0/2 probaron 32 y después 128 plazas; la cohorte 1 invirtió el orden. Las seis pruebas consumieron el mismo vector de 19.840 ofertas: 320/s, 1 s de calentamiento, 60 s de medición y 1 s de enfriamiento; 1.000 cuentas y exactamente el 80 % de los orígenes entre 50 cuentas calientes. No son dominios físicos independientes de disponibilidad.

La tabla registra las seis pruebas. De 119.040 ofertas, 118.887 terminaron confirmadas y reconocidas, 153 encontraron el límite de admisión y ninguna tuvo excepción ambigua. Los rechazos se produjeron exactamente con 32 plazas activas: 129 durante el calentamiento y 24 durante la medición. Con 128 plazas no hubo rechazos. La reconstrucción independiente de operaciones, apuntes, saldos y outbox superó las siete invariantes en cada prueba: 42 comprobaciones. La tasa SQL procede de marcas del servidor dentro de una ventana conservadora, no del número de ACK; sus fronteras pueden incluir commits de ofertas de una fase contigua. Por ello 320,0167/s no altera el contrato de 320 ofertas/s. La fase de la oferta y la ventana temporal SQL son magnitudes distintas.

Con 128 plazas, los máximos durante el calentamiento fueron 51, 93 y 92; durante la medición, 26, 17 y 6. Con 32 plazas, los máximos de medición fueron 32, 6 y 10. Ampliar el límite permitió admitir todas las ofertas en estas observaciones. El orden invertido no elimina la variabilidad del runner ni identifica saturación del servidor. Tampoco explica retrospectivamente los 12 rechazos históricos: aquel cliente no registraba los instantes exactos de decisión y liberación.

Se conservan retrasos de decisión de todas las ofertas, demoras entre finalización y liberación, CPU, memoria, GC y observaciones de espera de PostgreSQL. La latencia de los supervivientes admitidos no constituye un p99 del servicio. Falta medir la espera exacta por conexión; mantener el pool en 32 no demuestra que sea el cuello de botella. No se demuestra capacidad de la ruta Orleans, escalado de silos, ciclo de vida natural de grains, HA física, rendimiento de producción, MIPS ni TCO. La instrumentación modifica los tiempos y la topología difiere de la campaña anterior con dos silos en Podman.

La auditoría congelada verifica los hashes de los ZIP y del código original, el vector completo, las trazas exactas de plazas y los estados SQL. Los PR compilan y comprueban los contratos; nuevas campañas vivas requieren ejecución manual. Una matriz omitida no equivale a una prueba ejecutada correctamente. No se ha relajado ningún criterio experimental. #25 y la aceptación global de E2 siguen abiertos.
