# M2 · Durable ledger behind REST and gRPC, local scale-out

**Language:** English-only engineering project. The book provides both Spanish and English explanations.

**First executable slice, not a production benchmark.** This experiment extends M1: REST/JSON and gRPC/Protobuf now call the **same** .NET 10/Npgsql implementation that commits to a real PostgreSQL 16.13 database. Both are HTTP/2 **without TLS** on the same GitHub Linux runner.

A Python harness resets a dedicated disposable E1 schema before each trial, executes **256 distinct transfers**, then uses the *separate read-only E1 oracle* to inspect persisted accounts, postings and outbox. It requires exactly 256 committed operations, 512 postings and 256 outbox events. The final negative control intentionally deletes a posting, requires oracle rejection, restores it and rechecks the ledger.

20 synthetic trials: REST and gRPC × uniform/50%-hot-account traffic × **1, 2, 4, 8, 16 local service processes**. Closed-loop concurrency 16, deterministic round-robin client routing, with a separate database shared by all processes. Each trial produces a JSON with committed operations/s, p50/p95/p99, distribution by replica and explicit limits. **Do not infer that more replicas improve performance**: a single DB and 2-core runner can become the bottleneck. These are not VMSS, AKS, Azure Container Apps, WAN, TLS or mainframe experiments.

Run from repository root after creating **a disposable PostgreSQL 16 database** with Podman (this tool drops tables):

```bash
podman run -d --name m2-pg -e POSTGRES_PASSWORD=m2local -e POSTGRES_DB=m2lab -p 127.0.0.1:55433:5432 docker.io/library/postgres:16.13
python3 -m pip install -r lab/e1_pg/requirements.txt
export E1_PG_DSN="host=127.0.0.1 port=55433 dbname=m2lab user=postgres password=m2local"
export E1_PG_NPGSQL="Host=127.0.0.1;Port=55433;Database=m2lab;Username=postgres;Password=m2local;Pooling=true;Maximum Pool Size=32"
python3 lab/durable_rpc/test_m2.py
podman rm -f m2-pg
```

**Evidence rules:** every CI job uploads `lab/results/m2/`. The original complete 20-scenario M2 execution report, independent SQL-oracle outcomes and CI provenance are now versioned in [M2 evidence](../../evidence/runs/M2.md). No change to the baseline COBOL/SQLite hashes. E1 remains partially verified; E3 remains unexecuted until representative infrastructure, open-loop offered load, capacity contract and WAN costs have been tested.

Next: equivalent TLS/mTLS; warm and cold service health; true distributed ingress, retries, cancellation, account-hotspot contention and N-1 failure; then Azure VMSS, AKS and PaaS cost per durable accepted transfer.
