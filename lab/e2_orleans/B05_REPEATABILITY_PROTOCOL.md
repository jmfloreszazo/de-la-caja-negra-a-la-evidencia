# E2-B05 repeatability pilot — fixed-clock real workload, NOT capacity

**Status: ORIGINAL CI VERIFIED as a bounded repeatability pilot; NOT a sustained-capacity benchmark.** [GitHub Actions #41204905763](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41204905763) passed on source SHA `6b546c99f31fdd42f96da9960408df5716dd36c6`. The [unaltered original artifact #13044531582](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41204905763/artifacts/13044531582) was downloaded and its ZIP SHA-256 independently checked (`93a7be851b9cd17f4e848cf1ca773c770e2ebc74bfcd651f7bba66f9b0cb4510`), along with all 24 raw client and SQL trial observations. See the [archived evidence](../../evidence/runs/e2-b05-repeatability-pilot.json). E2 overall remains `partially_verified`.

## Goal and experimental slice

Advance the previously verified B05 4-second smoke to a **bounded matched-route repeatability pilot**, retaining one durable PostgreSQL ledger and an independent SQL observer. Do not claim a sustained throughput ceiling, production p99, Azure or IBM Z capacity equivalence.

| Parameter | Predeclared value |
| --- | --- |
| Source profiles | uniform and 5%-eligible-hot (80% of intents originate from IDs 1..50) |
| External offered rates | 20 and 40 operations/second, fixed-clock arrival |
| Repetitions | 0, 1, 2 for each profile/rate |
| Routes | direct PostgreSQL and Orleans account grain |
| Phases | 1-second warm-up, 8-second measurement, 1-second cooldown |
| Total trial cases | 2 profiles × 2 rates × 3 repetitions × 2 routes = **24** |
| Offers | 200 or 400 per trial; **7,200** total scheduled across all trials |
| Topology | two live Orleans silos, PostgreSQL, separate .NET client; four separate Podman network namespaces on **one physical Ubuntu runner** |
| Maximum concurrently executing | 32; a missed offer is recorded, not silently delayed |
| Authoritative outcome | separately queried PostgreSQL operations, postings, outbox, account balances and 7/7 independent ledger checks |

The same source vector bytes must be used for direct and Orleans for each profile/rate/repetition, with reset **between trials only**. Each request ID and fixed scheduled monotonic deadline is preserved. An early dispatch, missing/duplicate operation, rejected/ambiguous acknowledgment, incomplete or duplicate posting, or independent SQL parity mismatch must fail the acceptance criteria. Preserve raw client JSON **before** applying assertions.

## Execution prerequisites

The workflow is opt-in for disposable Podman, with loopback-only published PostgreSQL port and two private bridges. The client must explicitly have E2_B05_SMOKE=1 and E2_B05_REPEATABILITY=1, alongside the existing 1000-account and E2 cluster opt-ins. The prior 4-second smoke remains a separate unchanged execution mode.

Run using Python 3.12, .NET 10, Podman and a disposable PostgreSQL image; the exact workflow is .github/workflows/e2-b05-repeatability.yml. Reproduce using `python3 lab/e2_orleans/test_b05_repeatability.py` only in the documented isolated fixture with the published app assembly and E2_PG_NPGSQL / E1_PG_DSN environment.

## Data interpretation and guardrails

**Source offering is not completed throughput.** The reported 20/40/s is the *scheduled arrival rate*, not a measured sustainable SQL COMMIT rate. Independent SQL checks at **run end** prove durable operation cardinality and parity, but do not timestamp each database commit within the 8-second measurement interval. The descriptive latency percentiles are end-to-end from *scheduled arrival* to client response. Only 8 measured seconds and three repetitions do not provide a reliable steady-state p99 or a saturation boundary.

Do not infer that Orleans is faster or slower from sequential routes on a single runner: thermal/cache effects, warm-up and order remain confounders. Do not hide a failed trial or silently replace a missing offer. No mainframe MIPS comparison, multi-host HA, cloud price or VM/AKS/PaaS TCO is licensed by this pilot.

## Remaining scientific acceptance after this pilot

- Increase measured windows to 60–300 seconds at multiple rates and account-skew profiles; preserve 3+ genuinely independent runner/host repetitions.
- Collect actual SQL COMMIT timing (or independently sampled PostgreSQL durable state) to distinguish completed throughput per interval from **work offered during** that interval and drained after it.
- Record PostgreSQL lock/deadlock/pool waiting, CPU, memory, .NET GC, network RTT and client utilization. Show true bottleneck and confidence intervals.
- Explore client overload, missed offers and ambiguity with explicit classifications and independent durable reconciliation rather than expecting 100% business acceptance at every load point.
- The original CI and independent raw-artifact audit now permit a narrowly scoped ES+EN **bounded pilot** evidence entry; they do not authorize a capacity claim. Do not promote E2 from partially_verified.

Published v2026.10.29 unchanged; issue #25 remains OPEN. All source and lab docs are English. Book editorial outcomes require both Spanish and English.
