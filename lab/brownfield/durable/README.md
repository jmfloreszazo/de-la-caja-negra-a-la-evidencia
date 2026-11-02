# Durable brownfield capability candidate — CAP-007 / CAP-005

**Status: IMPLEMENTED SOURCE, NOT YET INDEPENDENTLY EXECUTED OR ACCEPTED.**
This is a disposable, synthetic PostgreSQL 16 + .NET 10/Npgsql 10.0.3
engineering candidate. It does not implement a real COBOL adapter, customer
authorization, customer policy, two-ledger reconciliation or production cutover.
No parser and no 1:1 COBOL translation are involved. TODM G6 remains BLOCK.

## Design boundaries

- `brownfield.authority` has one synthetic writer (`legacy` or `candidate`)
  and an epoch. Each transfer holds `FOR SHARE` until the SQL transaction ends.
  A switch takes `FOR UPDATE`, waits for open transactions and increments the
  epoch. This fences this shared database command path **only**: it does not
  fence an actual CICS/Db2 incumbent or external payment processors.
- `brownfield.commit_clock` is deliberately a separate SQL row: a transaction
  updates the clock without upgrading its shared authority lock.
- A stable operation ID and deterministic SHA-256 request fingerprint are stored
  with every COMMITTED or REJECTED decision. Reuse with a different request is
  `ID_CONFLICT`; a matching replay is `DUPLICATE_*`. A crash cannot create
  half a transfer: operations, postings, outbox and account balances share one
  PostgreSQL transaction.
- CAP-005 reads the **authoritative** SQL balance and an explicit watermark.
  It returns `BELOW_MINIMUM_VERSION` if the requested minimum is not satisfied.
  No read-model projection or change-data-capture lag is implied or measured.
- Authorization is only a fixed `mandate=SYNTHETIC` fingerprint fixture, not a
  real mandate, authentication, KYC/AML rule or product policy.
- All operations are integer EUR minor-units for 16 seeded accounts. This cannot
  represent FX, holds, value dates, rejected reversals or real bank cut-off rules.

## Reproduce on a **disposable** database only

Do not run the following against E1/E2, shared or customer databases.
`test_durable.py` **drops the entire `brownfield` schema**, after checking
the actual database name starts with `bf_`. Port and password are local fixtures.

```bash
podman run -d --name bf-pg -e POSTGRES_PASSWORD=bflocal \
  -e POSTGRES_DB=bf_lab -p 127.0.0.1:55437:5432 \
  docker.io/library/postgres:16.13

python3 -m pip install -r lab/e1_pg/requirements.txt
export BROWNFIELD_DISPOSABLE=YES
export BROWNFIELD_PG_DSN='host=127.0.0.1 port=55437 dbname=bf_lab user=postgres password=bflocal'
export BROWNFIELD_PG_NPGSQL='Host=127.0.0.1;Port=55437;Database=bf_lab;Username=postgres;Password=bflocal;Pooling=false'
python3 lab/brownfield/durable/test_durable.py

# Examine independently generated local-only evidence; it is not original CI.
cat lab/results/brownfield/durable-summary.json
podman rm -f bf-pg
```

After `test_durable.py` has initialized the disposable schema, the standalone
CLI accepts the following calls (values are synthetic):

```bash
dotnet lab/brownfield/durable/DurableBank/bin/Release/net10.0/DurableBank.dll \
  balance 1 0

# CLI syntax:
# transfer <operation-id> <source> <destination> <amount-minor> <writer> <epoch> [fault]
# balance <account-id> <minimum-global-version>
# switch <expected-writer> <expected-epoch> <target-writer> <expected-watermark> <expected-operation-count>
```

## Independent failure controls

The external harness compiles its own candidate and checks the saved SQL state
with a separate Python/psycopg oracle after each relevant phase:

1. Duplicate ID, changed request, insufficient funds and hot-account races.
2. Process exit after COMMIT before the original response, then replay.
3. Process exit after debit before COMMIT, and **Linux SIGKILL** while an
   uncommitted debit is open, then verify rollback and retry.
4. Stale epoch fencing, SQL writer switch, switch back, and stale minimum version.
5. Delete a committed posting on the disposable fixture and verify the
   independent oracle **fails**, restore it and require recovery.

`oracle.py` checks source-independent persisted account conservation, each
operation's balanced postings, outbox cardinality, rejected-side-effect absence,
watermarks and authority metadata. It is a technical oracle, **not** a signed
business Golden Master. Results are not accepted until original source-head CI
jobs execute the real PostgreSQL tests and produce auditable immutable raw
artifacts. Ordinary Book or offline Lab checks alone are insufficient.

See the [English engineering note](../../../docs/BROWNFIELD_DURABLE.md) and
[Spanish engineering note](../../../docs/BROWNFIELD_DURABLE.es.md), and
[tracking issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58).

## Explicitly outstanding

Actual black-box legacy adapter; source/target independent reconciliation;
external legacy authority shutdown/fencing; out-of-order CDC and read-model lag;
real bank mandate and Golden Master approval; genuine G2/G6 human acceptance;
cross-host faults, PostgreSQL HA, p99/SLO capacity, production recovery
semantics and dated economics. E2 remains separately partially verified.
