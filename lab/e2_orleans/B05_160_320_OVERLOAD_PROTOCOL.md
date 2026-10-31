# E2-B05 — disposable 160/320 offered-rate open-loop overload experiment

**Predeclared protocol now supported by original CI and independently checked ZIP evidence — NOT a sustained saturation ceiling or IBM Z MIPS reference.** [Original CI #41213914581](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41213914581) passed **15/15 checks** on source SHA `d21af6e595ed790834280787ff53a41bb301e65c`; the [original artifact #13047313472](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41213914581/artifacts/13047313472) was downloaded and rechecked against SHA-256 `376f8053d3f70012a6ca2ad4088aa0f05ae71a57542ceb5fe027f6ce282837ce`. **59,520 offered intents / 59,508 PostgreSQL COMMITs, 119,016 postings, 59,508 outbox, 28/28 SQL Oracle Gates**. The only **12 missing** offered IDs were never admitted during **320/direct warm-up at 0.100–0.134s**, NOT during the measurement window. Independent SQL recorded **160 or 320 COMMIT/s in the 60-second window** on both routes. The 320/direct final-state SHA differs from 320/Orleans because 12 warmup offers were never executed; this is not an unexplained ledger violation. The [immutable ES/EN scientific record](../../evidence/runs/e2-b05-160-320-sql-overload.json) preserves the negative instead of hiding it.

## Objective / limits

Try to falsify the hypothesis that a single physical Linux runner hosting the PostgreSQL 16.13 ledger, two .NET 10 Orleans silos and the external fixed-clock client can accept all offered **160 or 320 intents/s** from the preregistered hot-source synthetic profile. A higher offered rate **may** overload the client, DB, source account grains, Npgsql pool or host. Any such overload must remain visible and not silently trigger retries or reduce workload size.

| Parameter | Fixed value |
| --- | --- |
| Offered rates | **160 and 320 intents/s** (NOT completed PostgreSQL COMMIT/s) |
| Routes | Direct IDurableLedger and Orleans persistent cluster client, same source vector per rate |
| Source profile | 1,000 synthetic accounts, exactly 50 eligible hot source keys, exactly 80% of source intents concentrated in that eligible 5% |
| Repetitions | One per rate and route (4 trials); no confidence interval or steady-state SLA |
| Per-trial phases | 1s warmup + 60s measurement + 1s cooldown (62s total) |
| Offered operations | 9,920 per route at 160/s; 19,840 per route at 320/s; **59,520 total scheduled** |
| Client cap | 32 concurrent admitted operations; a full cap records MISSED_OFFER_INFLIGHT_LIMIT and does not turn open-loop into closed-loop waiting |
| Strict opt-in | `E2_B05_SMOKE=1`, `E2_B05_COMMIT_WINDOW=1`, `E2_B05_OVERLOAD_SWEEP=1`, `E2_NETWORK_TEST=1`, `E2_MAX_ACCOUNT_ID=1000` |
| Bounds | 20,000 intents per trial, `160/320` exact rate gate, 90s maximum scheduled time (client drain bounded by CI/process timeout) |
| SQL evidence | PostgreSQL `track_commit_timestamp=on`, unique persisted operation IDs, per-operation server `pg_xact_commit_timestamp(xmin)`, conservative certain/possible in-window rates + 60 one-second bins |
| Independent Oracle Gates | Seven business/ledger invariants on the authoritative SQL state, two postings and one outbox for each durable operation |

## Observation / negative criteria

1. Archive original *external-client JSON before* asserting anything about financial correctness, including **every offered ID** whether never dispatched, acknowledged or ambiguous.
2. Query PostgreSQL after the full trial; an ACK with no SQL COMMIT or a COMMIT for an undispatched offer is a **CI failure**. No SQL operation ID can appear twice and every COMMIT must have the exact paired postings and outbox event. A client exception **may conceal a durable COMMIT**; count it as ambiguous-but-durable instead of treating it as an automatic rollback. No financial transaction is replayed as a silent benchmark retry.
3. An in-flight-slot miss or ambiguous exception **is a valid negative load observation** when independent SQL, accounting and origin identity are internally consistent. The measured completed PostgreSQL COMMIT window rate must be derived from *server timestamps*, not ACKed or offered intents.
4. p50/p95/p99 from ACKs are descriptive **survivor-biased distributions** if any offers miss/timeout: report censoring counts and never call them a complete service SLO. Preserve dispatch lateness and per-second server COMMIT histograms rather than claiming a uniform response.
5. Capture supplemental `pg_stat_database` totals, but they include membership/oracle traffic, not just synthetic business COMMITs. Do not use them as business TPS, and do not infer specific lock bottlenecks from database-wide counters alone.
6. Each direct/Orleans source input SHA must match. Their final durable SQL state hashes are required to match **only if both routes completed all offered work**; incomplete work is reported, not discarded.

## Explicit exclusions to E2 closure

This is **one repetition per route/rate on ONE physical runner**, no true host/failure-domain isolation, no physically independent client generator, no simultaneous multi-host PostgreSQL HA, no pool-wait or network/CPU/GC causal bottleneck attribution, and no 3+ independent runner cohorts or production p99 guarantees. Two above-baseline offered rates alone do not establish a sustainable saturation knee or accepted horizontal scaling. A correct CI run merely verifies the claimed scope; any observed limit must be replicated and distinguished from an artificial **32 in-flight client cap**.

Accepted project result requires full original workflow provenance, raw artifacts, independent re-audit and then bilingual ES/EN editorial evidence. E2 overall remains `partially_verified`, [issue #25](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/25) remains open, and published `v2026.10.29` is unchanged. F10 C01 placement and C04 gateway isolation are separate issues; this branch does not modify them.
