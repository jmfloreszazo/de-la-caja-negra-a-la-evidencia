# E2-B05 — PostgreSQL server-recorded COMMIT timestamps over a 60-second window

**First one-host, one-rate 60-second slice ORIGINAL CI VERIFIED; NOT a capacity ceiling.** Source [PR #41](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/41) merged on commit `c310b805e35e6afafd8df7c3a8196cd8e68c8f1c`. Original [GitHub Actions #41207978844](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41207978844) passed 13/13 checks; raw [artifact #13044689170](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41207978844/artifacts/13044689170) ZIP SHA-256 `4b2d444fedd8da5e064c117ebe5f7e7fc75727bb24d931649f5c4702860c88ac` independently verified. Each trial has exactly **1,200 certain SQL-recorded COMMITs per 60 seconds = 20.0 measured PostgreSQL COMMIT/s**, 20 per 1-second bucket, 4,960 total durable transfers and 28/28 independent SQL oracles. The [archived evidence](../../evidence/runs/e2-b05-sql-commit-window-60s.json) is narrowly scoped to this load point and this one physical host. E2 remains `partially_verified`; issue #25 remains OPEN; published `v2026.10.29` unchanged.

## Hypothesis / narrow scientific objective

The previous B05 pilot established durable cardinality **after each trial**, but 20 or 40 *scheduled intents/second* were not measured PostgreSQL COMMIT rates. This slice independently retrieves PostgreSQL 16 transaction COMMIT timestamps, without relying on Orleans or client ACKs, and measures bounded per-window durable confirmation counts. It is deliberately **not** a saturation-capacity or mainframe MIPS test.

PostgreSQL reference: https://www.postgresql.org/docs/16/functions-info.html — the documented committed-transaction function `pg_xact_commit_timestamp(xid)` requires `track_commit_timestamp=on`. Database source: https://www.postgresql.org/docs/16/transaction-id.html . In this disposable PostgreSQL 16.13 instance only, start the server with `postgres -c track_commit_timestamp=on`; do not silently assume this is enabled in an existing production system. Commit timestamp information may be lost during vacuum/freeze or XID history maintenance and is not an eternal transaction audit log.

## Pre-registered schedule and limits

| Dimension | Value |
| --- | --- |
| Source profiles | Uniform and exactly fifty eligible hot accounts (80% of source intents on IDs 1..50) |
| Routes | Direct Npgsql/PgDurableLedger versus persistent external Orleans client (same source vector for each pair) |
| Offered arrival rate | **20 intents/second** only; NOT measured COMMIT TPS |
| Repetitions | One per profile and route (total **four trials**) |
| Time per trial | 1s warmup + **60s measurement** + 1s cooldown |
| Offered requests | 1,240 per trial; total **4,960** scheduled intents |
| Concurrency limit | 32 outstanding requests; admission failure recorded as missed, never hidden |
| Topology | One physical GitHub Ubuntu runner, four network namespaces: PostgreSQL, primary, secondary, and external client |
| Independent SQL | For every operation ID, query `pg_xact_commit_timestamp(xmin)` on the authoritative `operations` row and archive its UTC time and source phase |
| Accounting gate | Every unique operation ID committed once, two postings and one outbox, seven independent SQL invariants, matching direct and Orleans state hashes |

## Window-boundary clocks and uncertainty

The external .NET client brackets `Stopwatch.StartNew()` with `DateTimeOffset.UtcNow` *before* and *after*. Its fixed-clock offered schedule is monotonic; PostgreSQL independently records COMMIT UTC timestamps. The fixture tests that a `clock_timestamp()` SQL sample lies within the local host UTC bracket ±100ms before and after each trial. The client, silos and database share **the same physical Linux kernel wall clock**; this *does not* establish cross-host clock synchronization.

For a client-clock origin bracket `[u0, u1]`, the 60-second measurement phase certainly begins **no earlier** than `u0+1s` and **no later** than `u1+1s`; it ends between `u0+61s` and `u1+61s`. Count a COMMIT as **certainly inside** only if its server UTC timestamp belongs to `[u1+1s, u0+61s)`; count it as **possibly inside** when it belongs to `[u0+1s, u1+61s)`. Publish both count/rate bounds, the clock-bracket duration and the **raw original per-operation COMMIT timestamps**. The result is therefore an independently SQL-observed interval, not a guessed value from operation acknowledgements.

For clarity: throughput in the measurement window may include late warm-up intents and omit delayed measurement intents; report both *all durable SQL commits in the window* and the subset of *measurement-phase offers* actually COMMITTED inside the window. An operation committed after the measurement interval still counts as durable **by run end**, not as in-window COMMIT throughput.

## Fail-closed rules

- Require PostgreSQL `track_commit_timestamp=on` before any financial request and compare PostgreSQL vs host UTC both before and after each trial.
- Missing COMMIT timestamp, non-monotonic client dispatch, unexpected operation ID, a missed or ambiguous request, unmatched postings/outbox, unequal direct/Orleans persisted state, or failed independent SQL oracle **fails the current case**; preserve the original client JSON and previous observations, plus the original failure diagnostic.
- Never rerun an individual financial transfer to make metrics look better; reset the disposable database **only between whole trials**.
- Do not claim physical high availability, cross-host failure domains, sustainable 20 COMMIT TPS, p99 SLA, Azure TCO, or mainframe MIPS equivalence from this first 60-second slice.

## Still needed to close issue #25

A statistically meaningful sweep to overload with 60–300s windows, 3+ independent physical runner cohorts at each rate, actual machine/cgroup/SQL wait-lock/connection pool/.NET GC and network telemetry, accepted/rejected/ambiguous work classification, p50/p95/p99 distributions and confidence intervals, plus independent hardware mainframe reference workload and dated Azure/on-prem pricing. E2 stays `partially_verified`; the book's scientific interpretation must be published in **both Spanish and English** after actual original CI evidence has been independently audited. Code and lab documentation are English-only.
