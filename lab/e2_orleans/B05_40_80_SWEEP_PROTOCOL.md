# E2-B05 — 40/80 offered-per-second hot-source exploration (60-second windows)

**FIRST corrected original CI and independent raw ZIP audit VERIFIED; NOT a saturation or mainframe-capacity result.** Source [PR #43](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/43) merged as `6c9f8ea9989cb8c572a1e5bc51f4004c95e4a1ca`, after **14/14 checks**. Corrected [CI #41210913483](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41210913483) uploaded [original raw ZIP #13045879294](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41210913483/artifacts/13045879294), independently verified SHA-256 `7ea9062c80dc92f1354f5076c543e3105d8a6ebfccac25c266c8398fe35dc262`. PostgreSQL independently recorded **40.0 and 80.0 COMMIT/s** in 60-second windows through both routes; 14,880 durable transfers by trial end, 29,760 postings, 14,880 outbox, 28/28 SQL oracle checks and zero missed/ambiguous offers. This is a bounded single-host two-load-point finding, **NOT a maximum capacity, statistically defensible p99 or MIPS reference**. See the [source-audited evidence](../../evidence/runs/e2-b05-hot-40-80-sql-sweep.json). E2 remains `partially_verified`, B05 issue #25 stays OPEN, published `v2026.10.29` unchanged.

## Scientific question

Can the same direct-ledger and Orleans-routed financial operations maintain durable correctness when a fixed-clock client **offers** 40 or 80 intents per second with **80% of sources selected from exactly 50 hot account IDs**? How many distinct PostgreSQL COMMITs actually land inside the 60-second window, and do missed admissions or ambiguous exceptions appear?

Unlike the previous success-only 20/s experiment, **load shedding and ambiguous client outcomes are measured data**, not a reason to silently drop the run or retry an operation. Financial integrity and impossible client/SQL attributions still fail closed.

## Pre-registered scope

| Dimension | Value |
| --- | --- |
| Routes | Direct PostgreSQL ledger and external Orleans client, same offered vector |
| Source distribution | 1,000 synthetic accounts, IDs 1..50 eligible hot; exactly 80% of source intents per phase from these 50 |
| Offered rates | **40 and 80 requests/second** independently; these are NOT COMMIT rates |
| Original trials | Two rates × two routes = **four** trials, no cherry-picking |
| Timing | 1-second warm-up + **60-second measurement** + 1-second cool-down |
| Scheduled intents | 2,480 or 4,960 per vector; 14,880 across the four route trials (40 × 62 × 2 + 80 × 62 × 2) |
| Physical topology | One Ubuntu Linux host, PostgreSQL 16.13, two live Orleans silos, external .NET 10 client, four isolated Podman network namespaces |
| Concurrency ceiling | 32 outstanding client operations; non-admitted offers recorded as MISSED, not queued |
| SQL COMMIT timestamp | `pg_xact_commit_timestamp(operations.xmin)` with explicit disposable `track_commit_timestamp=on` |
| Financial oracle | Independent seven SQL invariants, balances/conservation, two postings + one outbox per authoritative COMMIT, no orphan effects |
| Source vectors | Immutable seed 20261031; direct/Orleans receive byte-identical operation IDs, amounts, scheduled times and profile |

## Method and acceptance

1. Pre-validate a disposable database and two independent real host-loopback SQL sessions. Preserve the PostgreSQL original failure logs on startup fault. Verify the same-host PostgreSQL wall clock and `track_commit_timestamp=on`.
2. Before each route, reset the fixture, restore 1,000 accounts and verify the independent SQL oracle. **Never reset during a trial** and never retry a financial operation to improve the result.
3. Dispatch every offered intent at its fixed monotonic target. When all 32 client slots are in use, record `MISSED_OFFER_INFLIGHT_LIMIT` (with no dispatched or completed timestamp). Record ACK and `AMBIGUOUS_EXCEPTION` as separate outcomes.
4. Preserve the **original raw client JSON before any SQL/timing assertions**. On process/SQL failure, archive a negative diagnostic and retain prior observations. Do not convert exceptions into no-op or rolled-back business outcomes.
5. Query the independent PostgreSQL state after the client process finishes, reconcile all SQL operation IDs against offered IDs, and require exact two-posting/one-outbox effects for **every durable COMMIT**. A client ACK without a durable COMMIT or an **undispatched offer with a durable COMMIT** is a correctness failure. An ambiguous client exception **may be durably committed** and must be counted as such, without pretending the client acknowledged it.
6. Read all surviving original server transaction COMMIT timestamps and count **certain/possible** 60-second interval COMMITs under conservative UTC start-brackets. Preserve a 60-bin histogram of server COMMIT timestamps, and explicitly distinguish measurement-phase requests durably completed **by run end** from transactions committed **inside** the measurement window.
7. Calculate client scheduled-to-ACK latency only for completed/acknowledged samples with the exact count of censored/missed/ambiguous samples. If any are absent, **do not report ACK-only p99 as service p99/SLA**. Preserve dispatch delay separately.
8. Require matched offered vector hash across routes. Require equal final persisted SQL state hashes **only if both route trials durably committed all offered operations**. Partial/overloaded results can differ, but must be accurately reported with original evidence.
9. Capture supplemental `pg_stat_database` counters before/after each trial as non-attributable host-wide diagnostics. They include membership/oracle/sampler SQL and must **never** be reported as business transaction COMMIT counts.
10. **CI success means observational/ledger contract and provenance validity only**, including a valid observed overload. It does **not** mean the system handled 80 durable COMMIT/s successfully, much less established a maximum sustainable capacity.

## Negative tests

The pure Python analysis has nine predeclared controls: ACK without SQL COMMIT, durable SQL operation for an offer never dispatched, an orphan/missing posting, invalid SQL oracle, early client dispatch, unknown outcome, duplicate SQL operation ID and drifted input digest, alongside a valid ambiguous-but-committed observation.

## Interpretation limits / next milestones

A single hot-account-skew profile, two high offered rates, one repetition per route and one physical CI runner are **exploratory, not statistically representative**. Thermal effects, sequential routes, and bounded client concurrency are confounders. This slice cannot establish a saturation knee, a production p99, a cross-host horizontal scaling curve or mainframe MIPS parity. Even if 80/s succeeds, E2 remains `partially_verified` and issue #25 remains OPEN. Next stage: multiple independent physical/runner cohorts at 20/40/80/160+ offered rates, full per-interval durable COMMIT curves, resource/lock/connection-pool/GC telemetry, confidence bounds and dated Azure/on-prem cost analysis.

No change to published `v2026.10.29`. All software code and lab documents in **English**. Any validated book interpretation requires **Spanish and English** with original source and SHA citation.

## Original negative/correction preserved

The first source run [#41210325810](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41210325810) successfully wrote all 14,880 original offers but incorrectly reported 7,440 in the predeclared summary metadata by omitting the second route when computing totals. Its original [artifact #13046247153](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41210325810/artifacts/13046247153) remains unchanged. The corrected program uses an explicit `assert expected_count == observed_count == 14880` across both offered rates and both routes, then reran on a separate GitHub runner. The first source C01 baseline regression [#41210325811](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41210325811) failed a precondition because all 16 probed grains were hosted by the secondary silo; see [issue #44](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/44). The corrected source-head C01 job subsequently passed; the cause of the original placement concentration is NOT established. Neither an incorrect metadata count nor a failed placement precondition may be hidden or described as a passed bank transaction.
