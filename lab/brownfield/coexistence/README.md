# Brownfield coexistence: synthetic legacy black box and candidate

**Status: SOURCE CANDIDATE — original two-store CI pending at first commit.**
This fixture is not a real COBOL, CICS, IMS or Db2 deployment. It tests
capability-level behavior without parsing or translating the original program.

## What is different from the durable single-store exercise

- **Legacy**: separate PostgreSQL 16.13 server/container, DB `bf_legacy`,
  with deliberately different tables `legacy.transactions`, `entries`,
  `notices`, `accounts` and `clock`. Executed via a separate Python
  CLI/process using a black-box transfer/balance contract.
- **Candidate**: another PostgreSQL 16.13 server/container, DB `bf_lab`,
  with the existing .NET 10/Npgsql `DurableBank` executable and schema.
- **Authority**: one `brownfield.authority` row in candidate PostgreSQL,
  cooperatively checked by both adapters for their transfer operations.
  The legacy adapter holds `FOR SHARE` on this row across the separate
  legacy database COMMIT. A cutover takes `FOR UPDATE`, waits for compliant
  in-flight writers and increments the epoch. This is **not 2PC**, HA, or
  fencing of an incumbent that does not cooperate.
- **Shadow**: performs read-only business predictions; it never runs a second
  transfer or outbox publisher. A stale candidate store must report mismatch.
- **Stage**: copies a consistent legacy SQL snapshot to the non-authoritative
  candidate store while holding the authority switch lock; never publishes
  financial events. The legacy remains writer until reconciliation is complete.
- **Reconcile**: independently normalizes and hashes every balance/version,
  operation/fingerprint/epoch/status, posting, outbox and decision watermark.
  Independent SQL double-entry checks must pass on **both** stores.
- **Cutover / rollback**: changes writer only when the complete snapshots agree.
  Candidate-origin decisions make the source stale; rollback then fails closed
  with `FORWARD_FIX_REQUIRED`. The protocol does not auto-migrate financial
  effects backward to the historical source.

## Gateway and fail-closed admission

The English-only [gateway](gateway.py) routes a capability command according to
the persisted candidate SQL authority and calls the legacy simulator through
its **separate external CLI**, not through a COBOL parser or shared internal
ledger implementation. `gateway.py transfer ID SRC DST AMOUNT` dispatches
exactly one compliant financial writer. `gateway.py balance ACCOUNT [MIN_VER]`
reads the currently authoritative store. Before cutover, a legacy balance
request with a nonzero minimum version is explicitly **rejected** because the
current legacy CLI does not implement that contract. `gateway.py shadow SRC
DST AMOUNT` performs a read-only comparison, never a second financial posting.

The test checks that the route changes after cutover and clean rollback,
that matching operation-ID replay remains a duplicate, and that an unmet
consistency parameter is not silently ignored. It also independently checks
that the two named databases have distinct PostgreSQL cluster identifiers.
**A privileged process with direct SQL credentials can still bypass this
cooperative gateway**, so the experiment does not prove production fencing.

## Exact disposable run

The harness **drops the legacy and brownfield schemas**. It refuses non-`bf_legacy` / non-`bf_lab` database names, requires
explicit loopback `127.0.0.1` ports `55438` and `55439`, and requires the opt-in.
Never point these commands to a shared database, real transaction engine,
customer data or production networks.

```bash
podman run -d --name bf-legacy-pg -e POSTGRES_DB=bf_legacy \
  -e POSTGRES_PASSWORD=bflocal -p 127.0.0.1:55438:5432 \
  docker.io/library/postgres:16.13

podman run -d --name bf-candidate-pg -e POSTGRES_DB=bf_lab \
  -e POSTGRES_PASSWORD=bflocal -p 127.0.0.1:55439:5432 \
  docker.io/library/postgres:16.13

python3 -m pip install -r lab/e1_pg/requirements.txt
export BROWNFIELD_DISPOSABLE=YES
export BROWNFIELD_LEGACY_DSN='host=127.0.0.1 port=55438 dbname=bf_legacy user=postgres password=bflocal'
export BROWNFIELD_PG_DSN='host=127.0.0.1 port=55439 dbname=bf_lab user=postgres password=bflocal'
export BROWNFIELD_PG_NPGSQL='Host=127.0.0.1;Port=55439;Database=bf_lab;Username=postgres;Password=bflocal;Pooling=false'

python3 lab/brownfield/coexistence/test_coexistence.py
cat lab/results/brownfield/coexistence/two-store-summary.json
podman rm -f bf-legacy-pg bf-candidate-pg
```

See [the bilingual research companion](../../../docs/BROWNFIELD_TWO_STORE.md)
and [Spanish companion](../../../docs/BROWNFIELD_TWO_STORE.es.md).

## Negative controls and omissions

The scenario **must reject** a switch if data change after staging or an outbox
event is missing. It also tests late/stale epochs, lost legacy and candidate
acknowledgements after COMMIT, candidate-origin writes preventing rollback, and
direct rogue legacy SQL writes *detected* (but not prevented) by the oracle.

There is no external admission/unknown-operation journal, durable coordination
across independent stores, IBM Z-side fence, streaming CDC, recovery from a
copy interrupted by power loss, physical-host independence, customer policy,
real business mandate, bank SLO, or TODM G2/G6 signoff. Both containers run on
the same CI runner. Never promote this to a production safety claim.

Code, lab protocols and README are in English. Research/book text is paired
in ES/EN. Issue [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58)
remains open after any narrow technical PASS.
