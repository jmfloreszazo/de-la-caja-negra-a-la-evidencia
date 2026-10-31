# E2-B05 — 40/80 offered-per-second hot-source exploration (60-second windows)

**Predeclared experimental protocol: NOT evidence, NOT an accepted saturation or mainframe-capacity result.** The proven 20.0 PostgreSQL COMMIT/s at 20 offered requests/s remains the only independently verified 60-second load point until original new CI and artifact audits succeed.

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
| Scheduled intents | 2,480 or 4,960 per vector; 7,440 across the four route trials |
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
