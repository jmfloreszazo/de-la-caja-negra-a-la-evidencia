# E2-B05: real external open-loop playback — bounded functional smoke

Status: **CANDIDATE ONLY UNTIL ORIGINAL CI PASSES**. This is a narrow prerequisite for issue #25; it is NOT a sustained-capacity benchmark.

## Test architecture

Four isolated private Podman namespaces on ONE GitHub-hosted Linux machine: PostgreSQL 16.13, two Orleans 10.4.0/.NET 10 silos, and a distinct client process/container. Both routes (direct ledger and Orleans account grain) run from the same external client environment, call the same authoritative PostgreSQL ledger, and reuse identical original offer-vector bytes. The account-grain path is not a separate distributed transaction.

## Preregistered run

- Two seeded profiles: uniform and five_percent_hot. Exactly 50 eligible hot accounts (IDs 1–50), 80% hot-source intents in the hot profile.
- 20 scheduled offers per second, 1-second warmup, 2-second measured phase, 1-second cooldown, 80 offers per route/profile. Four route/profile combinations = 320 *scheduled* real business intents.
- The external host/Orleans client is initialized BEFORE scheduling. Each fresh client persists through all 80 offers; process startup is excluded from offer latency. Each scheduled intent is dispatched on its absolute offset independently of previous responses. With 32 concurrent slots, an overfull offered arrival must be labeled MISSED_OFFER_INFLIGHT_LIMIT, not silently delayed.
- Store scheduled, dispatch and completion offsets in monotonic nanoseconds; client result, durable ledger status, retry count and ambiguous exception. Require all 80 dispatched and acknowledged COMMITTED with zero ambiguous/missed cases at this low-rate smoke.
- An **independent SQL observer** must confirm 80 COMMITTED operation rows, exactly 160 postings and 80 outbox rows with the precise stable operation IDs for EVERY route/profile. Require 7/7 independent Oracle Gates after each route, 1000 accounts with unchanged total balance, and identical full four-table persisted-state hashes between direct/Orleans per profile.
- Preserve source hashes, original vector, topology/namespace IDs, SQL membership, live client samples, failure diagnostics and original CI artifacts. No hand-edited result can count as CI evidence.

## Reproduction

Run on a disposable Linux machine equipped with Podman, .NET 10 and PostgreSQL oracle dependencies, from repository root:

    export E2_NETWORK_TEST=1
    export E1_PG_DSN='host=127.0.0.1 port=55435 dbname=e2lab user=postgres password=e2local'
    dotnet publish lab/e2_orleans/OrleansLab/OrleansLab.csproj -c Release --disable-build-servers -o lab/results/e2f10/app
    python3 lab/e2_orleans/test_b05_external_smoke.py

Authoritative CI workflow: .github/workflows/e2-b05-external-smoke.yml.

## Non-claims / remaining work

This smoke is 4 seconds per route/profile, with 80 samples per run. A descriptive p99 over 80 values is **NOT** a sustained p99 or saturation point. The two silos, client, and PostgreSQL share ONE physical runner; no separate physical fault domain, multi-host capacity, production RTO, 1/2/4/8/16-silo scaling curve, SQL pool/lock diagnosis, dated Azure cost, IBM Z MIPS or mainframe workload parity is tested. Issue #25 and overall E2 remain open/partially_verified.

A later B05 capacity phase needs a repeated offered-TPS sweep, 3+ independent long runs at each point, precise offered/dispatched/acknowledged/durable-commit accounting, queue depth and explicit lost/late offers, real host/SQL/Orleans resource counters, and confidence intervals. Keep published v2026.10.29 unchanged. All lab source and readmes English; book interpretation ES/EN only once original data supports it.
