# E2-F10-C03 — SQL-only partition of an active Orleans silo

Status: **original GitHub-hosted CI slice verified, E2 overall partially_verified**. Source run [#41136779085](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41136779085) at commit c91959521e7b10934f10f47e30f09496f555056a, [unaltered raw artifact #13017097945](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41136779085/artifacts/13017097945), independently downloaded ZIP SHA-256 9d66d1168d311e4363ef333a2707a29310845a60527c9deb2b053355628b28fe. See the [archived summary](../../evidence/runs/e2-orleans-sql-partition.json) and [strict validator](../../scripts/check_e2_sql_partition_observations.py).

## Hypothesis

A live Orleans 10.4.0 secondary silo loses network egress to its authoritative PostgreSQL 16.13 database while application-to-application transport stays up. A failed or timed-out client request is *not* a durable COMMIT acknowledgement. During the SQL cut, the independent host-side PostgreSQL observer must see no new operation, posting, or outbox record, and seven independent Oracle Gate invariants must remain true. After connectivity restoration, the same stable operation ID can be reconciled or retried to exactly one durable transfer.

## Test topology and fail-closed criteria

- Four separate Podman network namespaces on **one** GitHub-hosted Linux machine: PostgreSQL, primary silo, secondary silo, external client.
- Two private, fixed subnets: application 10.78.30.0/24 and SQL 10.78.31.0/24; no external database; PostgreSQL published to host loopback 127.0.0.1:55435 for independent inspection.
- Strict opt-in E2_NETWORK_TEST=1; ADO.NET clustering and disposable e2lab database only.
- Fresh, unpooled, bounded SQL health probe in ClusterModes.cs. A false SQL health result must not short-circuit gateway reachability observation.
- Actual tc/netem 100% packet loss on the secondary container's identified SQL egress interface, injected by a disposable network helper sharing that container's namespace.
- Before/during/after observations must show actual primary/secondary/client gateway reachability, the victim's unchanged process/container/network identity, and the victim SQL health transition from true to false and back to true.
- One baseline transfer genuinely hosted by the secondary. During the SQL cut, submit a new stable-ID transfer from that account through an independent Orleans client. Require either a real grain-side exception marker or Orleans timeout diagnostics proving the precise secondary activation is currently executing the Transfer method. Require no COMMITTED acknowledgement while disconnected. A 30-second timeout proves neither rollback nor eventual durability.
- Observe PostgreSQL operations, postings, outbox, and seven independent SQL invariants **while the fault is active**. Any durable effect or false success acknowledgement fails this case.
- Restore the SQL interface in a finally-protected cleanup path. Retry the same stable ID; accept COMMITTED or DUPLICATE_COMMITTED only if the independent SQL ledger converges to exactly two total operations, four postings, two outbox events, and one operation for that retry identity.
- Preserve original success JSON or full failed-step diagnostics with timestamps, netem qdisc details, process IDs, membership snapshots, source hashes, and the raw CI artifact.

## Reproduction

From the repository root on a Linux runner with .NET 10, Python 3.12, Podman and the PostgreSQL Oracle requirements installed:

~~~bash
export E2_NETWORK_TEST=1
export E1_PG_DSN='host=127.0.0.1 port=55435 dbname=e2lab user=postgres password=e2local'
dotnet publish lab/e2_orleans/OrleansLab/OrleansLab.csproj -c Release -o lab/results/e2f10/app
podman pull docker.io/nicolaka/netshoot:v0.13
python3 lab/e2_orleans/test_podman_sql_partition.py
~~~

Authoritative automated run: .github/workflows/e2-f10-sql-partition.yml.

## Explicit exclusions

This test does **not** prove separate physical failure domains, PostgreSQL HA, Orleans split-brain fencing, symmetric partitions, geographical recovery, production RTO, sustained TPS, or mainframe MIPS equivalence. A client timeout remains ambiguous until independent SQL reconciliation. The PR must not modify the existing published release or promote E2 overall above partially_verified.

Book/editorial findings must be authored in Spanish **and** English once the experiment is independently verified; this executable laboratory, script and README are English-only.
