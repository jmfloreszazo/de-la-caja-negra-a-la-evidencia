# B05 direct-client slot diagnostic

Status: executed three-cohort diagnostic; originals independently audited.
Tracks #25. The accepted ledger, historical client, workload generator and
oracles remain unchanged. This is a separate instrumented executable.

## Fixed initial question

The historical 320/s direct trial missed 12 warm-up offers under a 32-slot cap.
Its samples lack admission-decision and slot-release timestamps, so do not
retrospectively reconstruct exact semaphore occupancy from completion times.
This diagnostic records ADMIT/MISS/COMPLETE/RELEASE with an ordered sequence,
actual monotonic timestamp and active slot count under the same accounting lock.
Every miss must occur at the configured full cap; every admitted offer must
complete and release exactly once. No waiting for a slot, silent financial
replay, offered-rate reduction or omission of missed offers is permitted.

## Preregistered comparison

- Three independent fresh GitHub runner cohorts, each one physical host.
- Direct route only; a native .NET client and Docker PostgreSQL 16.13. This is
  a different topology from historical two-silo Podman runs and does not
  retrospectively explain their losses.
- Exactly 320 offered/s, 1s warmup + 60s measurement + 1s cooldown: 19,840
  scheduled intents per trial. Same fixed-seed vector and IDs in all cohorts.
- 1,000 accounts, exactly 80% of source intents on 50 eligible hot accounts.
- Compare client caps 32 and 128; keep Npgsql pool maximum 32 and durability
  settings fixed. Even cohorts run 32 then 128; odd cohort reverses the order.
- Reset SQL between trials and start a fresh client process. Do not prewarm
  away the cold-start window or retry a failed trial until it succeeds.
- Capture all per-offer timing, complete slot trace, per-second SQL wait/state
  samples, process CPU/GC/RSS observations, SQL rows/server COMMIT timestamps,
  source hashes, runtime/image identity and original failures.

The read-only independent 1,000-account oracle must return 7/7 per final state;
each COMMIT must have two postings and one outbox. The existing SQL COMMIT-window
analyzer reconciles all offered IDs, ACKs, ambiguous results and missed offers.
Raw client data is saved before SQL assertions. All-offer decision-lag
percentiles include misses. ACK-only latency remains explicitly censored when
offers are missed/ambiguous; it is not a complete service p99.

## Acceptance and limits

An internally consistent cap miss or ambiguous result is an observation, not a
reason to discard a trial. Invalid occupancy, missing release, early dispatch,
impossible ACK/SQL effect, malformed trace or broken oracle fails the run.
Three passing diagnostic cohorts establish bounded trace/SQL integrity at one
offered load point; they do **not** establish a capacity knee or prove that a
particular backend is saturated. A fixed pool of 32 can itself queue calls
when the admission cap is 128; exact pool-wait attribution is not measured.
Instrumentation changes timing. PG wait samples are descriptive observations,
not a causal bottleneck attribution. No Orleans-route performance, independent
physical load host, multi-silo scale, production SLA, Azure TCO or MIPS parity
is accepted. Keep #25 and E2 partial until the remaining gates are exercised.

```bash
python3 -m unittest discover -s lab/e2_b05_dispatch -p test_analysis.py -v
```

The first three-cohort campaign is frozen in [the evidence report](../../evidence/runs/B05-DISPATCH-DIAGNOSTIC.md). Run `python3 scripts/check_b05_dispatch.py` from the repository root to audit its originals. PR checks compile the client and run adversarial slot controls; the live matrix now requires manual workflow dispatch. Archive audits never count skipped live trials as PASS.

External capacity validation is a [documented follow-up](../../docs/EXTERNAL_VALIDATION.md), not an integration blocker. Keep this loopback fixture frozen; a distributed campaign needs a new endpoint-safe driver and per-host telemetry. Its scientific claims remain partial.
