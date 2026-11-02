# E2-B05 — Fixed-clock offered-load contract (offline precursor)

**Status: GENERATOR AND UNIT TESTS ONLY; NO BENCHMARK EXECUTED.** This protocol is a prerequisite to issue #25, not a capacity experiment. No TPS, p99, saturation, Azure cost, physical HA or mainframe MIPS equivalence claim is allowed from these files.

## Why B01–B03 are insufficient

Previously verified E2 B01/B02/B03 used 100 transfers per profile and route within a **single Orleans co-hosted process**. ArrivalOffsetMs is limited to 30 seconds, and the brief workload cannot establish a sustained performance limit. Its synthetic 7/7 SQL oracle and six matched route/profile results are valid in their narrow boundaries but are not B05 capacity evidence.

## Fixed external offer vectors

The Python script b05_arrival_contract.py produces an **offline JSON vector** for a separately implemented load generator. It never contacts SQL or Orleans and never asserts a benchmark PASS. Each operation has a stable ID, source/destination, amount, workload phase and integer nanosecond *scheduled* arrival relative to a monotonic hypothetical run start. Identical vector bytes must be used for direct and Orleans routes at each matched workload point.

Pre-registered source profiles:

- uniform: independent seeded random sources across IDs 1..1000; no guarantee of equal observed requests per account.
- five_percent_hot: **exactly 50 eligible hot accounts** (IDs 1..50), 80% of scheduled source intents from that set **per phase**, 20% from 51..1000. All 50 hot accounts are visited when at least 50 hot intents exist.
- one_account_half_intents: exactly 50% of source intents from account 1 **per phase**; 50% from IDs 2..1000.
- crossed: 1→2 and 2→1 in equal counts; a contention fixture, not a representative bank population.

Source and target differ, amounts are 1 cent, and opening balances are 100000 cents as in the existing 1000-account fixture. Phase offer counts must be divisible by ten wherever exact hot proportions are claimed: fail closed rather than round misleadingly. Standard seed 20261031; repetitions 0/1/2 give independently seeded but reproducible inputs. The direct/Orleans route is **not encoded** into operation IDs or vectors.

## Reproduce offline prerequisite

From the repository root with Python 3.12+:

~~~bash
python3 -m unittest discover -s lab/e2_orleans -p 'test_b05_arrival_contract.py' -v
python3 lab/e2_orleans/b05_arrival_contract.py \
  --profile five_percent_hot --offered-tps 100 \
  --warmup-seconds 10 --measurement-seconds 60 --cooldown-seconds 10 \
  --seed 20261031 --repetition 0 \
  --output lab/results/e2b05/contract/hot-r0.json
~~~

The dedicated CI workflow .github/workflows/e2-b05-contract.yml checks **only** deterministic contract generation and uploads original offline vectors. Its success is NOT measured performance, a sustained load SQL-oracle pass, or an executed B05 run.

## What the real B05 benchmark STILL needs

1. An **independent load generator** process or machine, separate from SQL and Orleans; persistent client connections and bounded queues. Do not launch a process per financial command.
2. **Open-loop playback** of every scheduled intent at its precomputed time, regardless of response completion. If an offer cannot be dispatched, count an explicit **missed offer**; do not silently delay the schedule. Preserve scheduled, actual dispatch, admission, response and independent durable completion times, plus errors and timed-out offers. End-to-end latency begins at **scheduled** arrival, not actual dispatch. Report dispatch lateness and in-flight depth.
3. Matched route conditions: identical vector SHA and seed, reset 1000-account dataset, PostgreSQL isolation/durability/locks, pool settings, resource limits, process topology and network route. Record runtime/container provenance.
4. A predeclared offered TPS sweep with warm-up and cool-down excluded from reported sustained metrics; at least three repetitions at each load point, abort/overload criteria and bounded client queues. Preserve **all** runs, including failures.
5. An **independent SQL oracle** per completed run, reconciling durable operation IDs vs acknowledgements, paired postings, outbox atomicity, conservation, nonnegative balances, projection and persisted-state hashes, plus negative control.
6. Real capacity results: durable committed TPS versus offered TPS; p50/p95/p99 and repetition uncertainty; rejection, timeout and retry rates; hot-key skew; CPU, memory, GC, SQL waits, locks, pool use and RTT. An offered schedule is **not** SQL throughput.
7. E3 cross-environment comparisons, later, must include priced and dated Azure/on-prem alternatives with real hardware evidence. No extrapolation from this offline vector to IBM Z MIPS.

Published v2026.10.29 remains unchanged. B05 stays OPEN and E2 stays partially_verified. Code and lab documents English-only; book/editorial findings in **Spanish and English** after genuine evidence exists.
