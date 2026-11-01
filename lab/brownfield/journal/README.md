# C2 durable admission/UNKNOWN journal — synthetic research

**CANDIDATE ONLY · NOT ACCEPTED · TODM G2=INCONCLUSIVE / G6=BLOCK.**

This bounded experiment adds an independent PostgreSQL 16 coordinator
(`bf_control`) to the existing `bf_legacy` and `bf_lab` containers.
It does **not** introduce a COBOL parser, financial 2PC, customer mandate,
production gateway or real IBM Z fence. The gateway session advisory lock
serializes one operation ID **only among cooperating gateway processes**;
the incumbent and candidate CLI can still be invoked directly. This known
bypass must be eliminated or externally fenced before a real migration.

Each operation persists admission *before* dispatch. An unknown response
remains `UNKNOWN` until a separate read-only source/target SQL oracle
finds a durable matching decision. Missing records are **not** rejected
operations. Cutover requires no unresolved or unjournaled effects and
independent normalized ledger agreement. Candidate writes forbid a
synthetic rollback; controller/target authority changes are **not atomic**
and need a separate crash-repair protocol. Never claim split-brain safety.

## Disposable setup

First use the two PostgreSQL containers and environment variables documented
in [coexistence](../coexistence/README.md). Add:

```bash
podman run -d --name bf-control-pg -e POSTGRES_DB=bf_control \
  -e POSTGRES_PASSWORD=bflocal -p 127.0.0.1:55440:5432 \
  docker.io/library/postgres:16.13
export BROWNFIELD_CONTROL_DSN='host=127.0.0.1 port=55440 dbname=bf_control user=postgres password=bflocal'
python3 lab/brownfield/journal/test_journal.py
podman rm -f bf-control-pg
```

**WARNING:** The test intentionally drops the `legacy`, `brownfield` and
`controller` schemas; every DB name is checked against its exact
dedicated fixture name. It writes no customer data. Read original CI run
artifacts rather than assuming that a successful PR description is evidence.

## Fault matrix

- `gateway-after-admit`: real process exit after durable ADMITTED;
  unresolved admission must block cutover
- `gateway-before-send`: real process exit after DISPATCHING;
  absence of SQL does not prove a safe rollback
- `gateway-after-send`: real process exit after remote COMMIT;
  recovery independently confirms the decision
- `adapter-lost-ack`: remote process exits after COMMIT;
  replay cannot produce a second posting/outbox
- Controller/candidate writer mismatch and forged terminal journal
  must be rejected
- Once the new candidate writes, rollback must fail closed

No cross-host failure domain, external payment switch, true authority
revocation, WAN, CDC, RTO/RPO, p99 benchmark or bank approval is proven.
All source, tests, CI and lab README are English; engineering discussion is
published separately in Spanish and English.

## Cooperating adapter fence (C2 only)

The C2 workflow sets `BROWNFIELD_REQUIRE_CONTROLLER=YES` and supplies both
`BROWNFIELD_CONTROL_DSN` (legacy Python) and
`BROWNFIELD_CONTROL_NPGSQL` (.NET candidate). Both adapters hold an SQL
`FOR SHARE` lock on the controller epoch through their financial COMMIT; a
missing controller rejects operations. The older two-store tests deliberately
omit these opt-in variables to preserve their historical reference behavior.

**Important:** direct invocation with valid coordinator credentials can still
write without a gateway journal entry. The independent audit detects this
but does not prevent it. An unsafe application that strips the opt-in guard
can also bypass it. A real incumbent requires a mandatory independent fence,
not simply this feature flag.

## Admission enforcement boundary

When `BROWNFIELD_REQUIRE_CONTROLLER=YES`, the financial adapters also
check the matching persisted `DISPATCHING` admission (ID, request hash,
accounts, amount, writer and epoch) before any new SQL ledger decision,
retaining the controller locks through COMMIT. Direct CLI calls with no
admission return `NOT_ADMITTED_BY_CONTROLLER`. The negative test then
explicitly disables the opt-in environment guard to demonstrate that the
historical permissive mode still bypasses this protection; independent
audit detects the resulting unjournaled effect. **Configurable cooperation
is not the same as revoking the actual mainframe writer.**
