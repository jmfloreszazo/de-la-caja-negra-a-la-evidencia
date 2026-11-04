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
export W01_LEGACY_DSN='host=127.0.0.1 port=55438 dbname=bf_legacy user=postgres password=bflocal'
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
