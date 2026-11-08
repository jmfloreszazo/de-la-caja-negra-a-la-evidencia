# M1 · gRPC/Protobuf vs REST/JSON: a reproducible transport-only experiment

**Status: executed and archived in the evidence registry. Not a bank transaction performance result.**

This is an independent .NET 10 test service exposing the **same stateless transfer decision** through:
- `POST /v1/transfer` with JSON over **HTTP/2**
- `banktransport.TransferApi/Submit` with Protobuf/gRPC over **HTTP/2**

Both calls run on the same loopback Kestrel process without TLS (h2c), **deliberately avoiding different TLS/network costs**. This is a microbenchmark of **request/response serialization and RPC transport overhead**, NOT the throughput of the PostgreSQL ledger. A separate expected-value oracle checks every reply; the harness deliberately presents an incorrect result and verifies that the oracle rejects it.

## Run with .NET 10 SDK

```bash
dotnet restore lab/transport/TransportLab/TransportLab.csproj
dotnet build lab/transport/TransportLab/TransportLab.csproj -c Release --no-restore
dotnet lab/transport/TransportLab/bin/Release/net10.0/TransportLab.dll benchmark 5088 2500 8 lab/results/transport/report-c8.json
python3 lab/transport/check_report.py lab/results/transport/report-c8.json
```

CI runs separate 2,500-request-per-round profiles at concurrency 8 and 32; each produces its own report. A single invocation starts the same loopback service and measures warmups then two recorded rounds per protocol, alternating the order. The benchmark logs p50/p95/p99, successful replies/s, concurrency, environment and a unique source commit. These are **closed-loop** rates, not open-loop offered load or real user/branch WAN latency. No throughput winner is asserted in advance: the implementation and measurement decide.

## Further evidence needed before applying the result to a banking migration

1. Repeat over equivalent TLS/mTLS (HTTP/2 for both), plus payload sizes from 100 B to 1 MiB, streaming, cancellation/deadlines and real network hops.
2. Run through realistic AKS/ACA ingress and load-balancing with long-lived HTTP/2 channels; scale service replicas 1, 2, 4, 8 and 16; account for per-RPC distribution.
3. Use the **same durable PostgreSQL ledger** behind both API paths, with hot-account contention, idempotency, and an independent read-only database oracle.
4. Run open-loop with queues, retries, node/route failures, and measure *durably committed* transactions/s, p99 branch-to-screen and full TCO—not just successful RPCs.
5. Compare functional parity and error semantics; **gRPC is not the opposite of HTTPS** (it uses HTTP/2, commonly secured by TLS). REST may also use HTTP/2.

The named packages are pinned: [Grpc.AspNetCore 2.84.0](https://www.nuget.org/packages/Grpc.AspNetCore/2.84.0), Grpc.Net.Client 2.84.0 and Grpc.Tools 2.84.0.

Recorded runs, original p99/throughput observations and their provenance are preserved in [the M1 evidence report](../../evidence/runs/M1.md) and checked in CI. These are local transport-only observations, not a cloud or banking-core benchmark.

## Reproduce through the common launcher

The existing Azure operator accepts `-Experiment m1`. The guest launcher builds
this project, runs both 2,500-request profiles at concurrency 8 and 32, then
executes `check_report.py` for each. It does not start a database or require a
container engine. A failed independent check stops the next profile.

For a local fresh-checkout campaign, M1 is opt-in so existing default campaign
sequences remain unchanged:

```bash
python3 lab/tools/reproduce_campaign.py --engine docker --experiments m1 \
  --output lab/results/m1-campaign --include-working-tree
```

The collector requires an explicit engine selection for its campaign metadata;
the M1 stage itself does not invoke that engine.

The [8 November Azure execution](../../evidence/runs/azure-m1-2026-11-08.json)
ran both profiles on the private North Europe D4s_v5 runner: eight measured
rounds, 20,000 responses, zero invalid/missing replies, both negative controls
passed. The report's `executionHost=AZURE_VM` identifies the machine;
`LOCALHOST_TRANSPORT_ONLY` identifies the loopback path on that machine.
These descriptions are compatible, not conflicting. Source commit and exact
source-archive digest are retained. The VM was deallocated after download.

Do not compare these short closed-loop response rates with durable transaction
capacity or declare a universal transport winner. Historical raw reports are
unchanged.
