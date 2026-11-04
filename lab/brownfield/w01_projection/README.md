# W01 — PostgreSQL read-only balance projection (synthetic brownfield)

**ENGLISH-ONLY EXECUTABLE LAB · CAP-005 · #32 · NO BANK APPROVAL**

This is a bounded two-PostgreSQL-server experiment. The existing synthetic
legacy fixture is the only authority for booked balance, financial transactions,
paired postings and notifications. A **separate projection PostgreSQL** holds
read-only copies of 16 synthetic account balances and a *source* watermark.
No parsers, 1:1 COBOL translation, customer records or financial dual-write.

**Important correctness boundary:** the projector does **not** implement CDC,
streaming or catch-up from an event log. A deliberately full, consistent
PostgreSQL source snapshot is copied into the target as a single SQL transaction.
The source transaction runs `REPEATABLE READ READ ONLY`. The target updates
account rows and stored watermark atomically; a failed rebuild cannot publish
half the balances under a newer watermark.

## Contract and refusal cases

- The source owns all updates. Read-model snapshots are **nonauthoritative**.
- Every read samples the current source clock before considering projection
  data. A matching, integrity-checked source watermark permits a *bounded*
  `PROJECTION_OBSERVED_CURRENT` result; it does NOT prove linearizability.
  A new source COMMIT can occur after the clock sample. The check adds a
  round-trip to the source; **no performance/scaling benefit is claimed**.
- Stale, missing or corrupted projection rows trigger an independent
  `AUTHORITATIVE_FALLBACK`, never a potentially outdated spendable value.
  If source clock or fallback read is unavailable, **BLOCK**; no stale
  financial reply is fabricated. A minimum watermark above source clock BLOCKs.
- Fallback is read from a **single source snapshot**. It is not ATM
  authorization, available funds or account-holder authentication.
- A repeat snapshot rebuild is idempotent. Moving source clock backwards or
  observing a changed source snapshot at the **same** clock fails closed
  during refresh; such a privileged source modification is *not detectable
  by watermark-only reads until an independent source observation*. This is
  a genuine open production risk, not an accepted silent bypass.
- The test-only synthetic source writer commits a balanced transfer and
  source clock update in **one PostgreSQL transaction**. The projector
  application source has no source mutation path. The independent test oracle
  checks conserved total, exact postings, outbox, clock and versions.
- No source-side fencing, source data completeness, business Golden Master,
  authentication, native IBM Z/CICS/IMS/Db2 integration, physical HA, CDC,
  production SLO, cross-region latency or TODM G2/G6 acceptance is proven.

## Run exact disposable fixture (Podman)

Run from repository root. The test script **DROPS and recreates** the schema in
the **strictly named disposable databases only**. It will refuse missing opt-in,
non-loopback and mismatched database names/ports. Never use any customer,
shared or production PostgreSQL.

```bash
python3 -m pip install -r lab/e1_pg/requirements.txt

podman run -d --name w01-source-pg -e POSTGRES_DB=bf_legacy \
  -e POSTGRES_PASSWORD=bflocal -p 127.0.0.1:55438:5432 \
  docker.io/library/postgres:16.13
podman run -d --name w01-projection-pg -e POSTGRES_DB=bf_projection \
  -e POSTGRES_PASSWORD=bflocal -p 127.0.0.1:55442:5432 \
  docker.io/library/postgres:16.13

export W01_DISPOSABLE=YES
# Test harness administration only: never pass this secret to a deployed reader.
export W01_LEGACY_ADMIN_DSN='host=127.0.0.1 port=55438 dbname=bf_legacy user=postgres password=bflocal'
# The test harness creates w01_reader and grants SELECT on accounts and clock only.
export W01_LEGACY_DSN='host=127.0.0.1 port=55438 dbname=bf_legacy user=w01_reader password=w01readerlocal'
export W01_PROJECTION_DSN='host=127.0.0.1 port=55442 dbname=bf_projection user=postgres password=bflocal'
python3 lab/brownfield/w01_projection/test_projection.py
cat lab/results/brownfield/w01/w01-original.json

podman rm -f w01-source-pg w01-projection-pg
```

After the tests, the last test leaves a disposable source and projection with
a committed synthetic transfer; the `projection.py refresh` and
`projection.py balance 1 --minimum-watermark 1` commands are available for
inspection **only while the disposable servers are running**. The CLI does not
create databases. Automated CI waits for both servers to accept connections
and keeps the full test logs, manifest and negative outcomes as an artifact.

## Source-reader least-privilege boundary

**Original exact-commit 20/20 PASS:** [GitHub Actions #41855993179](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41855993179) and [EN audit](../../../evidence/runs/W01-READER.md) / [ES audit](../../../evidence/runs/W01-READER.es.md), proving only **restricted SQL reader grants on the disposable source fixture**. The previous 16/16 run is preserved independently.

**New technical control:** the projector no longer accepts the PostgreSQL
`postgres` superuser as its source credential. It requires a named,
non-superuser `w01_reader` login and verifies the effective database role
and actual SQL privileges. This login has `USAGE` on the `legacy` schema
and `SELECT` only on `legacy.accounts` and `legacy.clock`; it cannot
update/insert/delete financial tables or read legacy operation/posting data.
The harness explicitly attempts an `UPDATE` after `SET TRANSACTION READ WRITE`
and expects PostgreSQL `42501 InsufficientPrivilege`, proving that merely
changing transaction mode cannot grant the source-writer permission.

A **separate test-harness-only** `W01_LEGACY_ADMIN_DSN` resets the named
disposable schema and performs synthetic source transfers and independent
accounting audits. The projector never imports this test harness or opens its
admin DSN. A subprocess test executes the read CLI with **only** the restricted
source DSN and target DSN, explicitly excluding the admin environment variable.
In real deployment, administrator credentials must not be accessible to the
reader process, its environment, secrets store or host; a fixture test alone
does not establish this isolation.

**Remaining limitations:** privileged writers can still bypass the source
clock; this negative test does not implement an incumbent-enforced fence or
bank-grade identity management. Projection reads still sample the source clock
and are not linearizable. The named password is **disposable test data only**,
never a production credential. [ES research](../../../docs/research/w01-reader-identity.es.md)
· [EN research](../../../docs/research/w01-reader-identity.en.md).

## What is independently tested

`test_projection.py` checks empty/stale fallback, first snapshot, committed
source write and lag, bounded-watermark read, full rebuild and idempotent replay,
corrupted projection and repair, same-clock source mutation rejected by
refresh, watermark regression, both failure modes, input and DSN guards,
separate PostgreSQL cluster identities and no source financial mutation by the
projector. Each test starts from two fresh, **disposable** DB schemas.

Original test output and SHA-based provenance are archived by
`.github/workflows/w01-read-projection.yml`. A source snapshot, a target
watermark and a green CI job are **not** an independently authorized bank
contract. Issue #32 remains open; W01 remains a structural/engineering slice
and #58 real incumbent fencing is a separate unsatisfied requirement.

**Original real-PostgreSQL CI 16/16 PASS (bounded synthetic scope):** [run 41853096276](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853096276) and permanent [EN evidence record](../../../evidence/runs/W01-PROJECTION.md) / [ES](../../../evidence/runs/W01-PROJECTION.es.md). No customer release or full scientific approval follows.

Companion research: [English](../../../docs/research/w01-projection.en.md) ·
[Spanish](../../../docs/research/w01-projection.es.md).
