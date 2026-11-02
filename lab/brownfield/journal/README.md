# C2 durable admission/UNKNOWN journal — synthetic research

**TECHNICAL CANDIDATE · NOT BANK ACCEPTANCE · TODM G2=INCONCLUSIVE / G6=BLOCK.**

This bounded experiment uses three PostgreSQL 16 containers: `bf_control`,
`bf_legacy` and `bf_lab`, on one CI runner. It models cooperative adapters,
not a real CICS/Db2 fence, customer authorization, financial 2PC or production HA.
The earlier [C2 observation](../../../evidence/runs/BROWNFIELD-JOURNAL.md)
remains historical evidence for its exact source SHA.

## Enrollment and admission

The test enrolls **fresh, empty fixtures** by persisting
`brownfield.authority.controller_required=TRUE`. Once enrolled, both the Python
legacy adapter and .NET candidate require the controller, even if
`BROWNFIELD_REQUIRE_CONTROLLER=NO` or controller variables are removed.
Reinitializing an enrolled controller through `reset-controller` is refused.
Fresh unenrolled fixtures retain the historical two-store behavior.
Existing populated schemas are not upgraded in place; start disposable fixtures
from the current schema. Interrupted enrollment leaves the latch enabled and
requires a fresh disposable setup, rather than permitting unjournaled traffic.

Before a financial decision, both adapters require matching `DISPATCHING`
admission: operation ID, fingerprint, accounts, amount, writer and epoch.
They hold controller authority/admission locks through the ledger COMMIT,
and recheck the persistent latch under the candidate authority lock.
A changed fingerprint conflicts; a lost ACK never authorizes a second writer.
Only independent persisted operation/posting/outbox evidence finalizes
`COMMITTED` or `REJECTED`. Missing decisions stay `UNKNOWN`.
`RECONCILIATION_REQUIRED` is persisted as well as returned to the caller.

The third-controller address is restricted to `127.0.0.1:55440/bf_control`
before connecting. Python address/service overrides and Npgsql alternative
hosts, ports and database names are refused. This is a disposable-data guard,
not an authorization system. Privileged raw SQL can still bypass application
checks, change the latch or reset the fixture; real writer revocation remains
an external prerequisite.

## Frozen transition and forward recovery

The pre-registered protocol is
`C2_SQL_ENROLLMENT_AND_FROZEN_FORWARD_RECOVERY_V1`.

1. Lock controller authority exclusively, drain cooperating adapters and
   require the journal-to-ledger audit to pass. Reject rollback after any
   candidate-origin decision, before freezing the controller.
2. Commit a `PREPARED` transition intent and `mode=SWITCHING` **before**
   staging or changing the candidate authority. Admission, dispatch and both
   adapters now refuse new financial commands.
3. Stage the source only while the candidate is non-authoritative. Compare
   normalized accounts, decisions, postings, outbox and watermark, then
   change the candidate authority once.
4. Under the same durable freeze, recover only the exact prepared old/new
   writer and epoch. Reconcile both stores and the admission journal before
   activating the controller and completing the intent in one controller
   transaction. An unexpected epoch or missing outbox leaves traffic frozen.

For a forward switch at epoch `e`:

| Boundary | Controller | Candidate authority | New financial admission |
|---|---|---|---|
| Before preparation | legacy / e / ACTIVE | legacy / e | Allowed with matching journal |
| Intent committed | legacy / e / SWITCHING | legacy / e | Blocked |
| Candidate COMMIT | legacy / e / SWITCHING | candidate / e+1 | Blocked |
| Controller completion | candidate / e+1 / ACTIVE | candidate / e+1 | Allowed with matching journal |

This is **recoverable cooperation, not atomic cross-database COMMIT**.
Recovery moves the prepared transition forward; it never guesses a rollback
from an absent reply. The candidate's older standalone `switch` CLI also
refuses authority changes after enrollment; use the journal coordinator.

```bash
python3 lab/brownfield/journal/journal.py switch candidate 1
python3 lab/brownfield/journal/journal.py recover-switch
```

## Disposable setup

Use the two containers and environment in
[coexistence](../coexistence/README.md), then add:

```bash
podman run -d --name bf-control-pg -e POSTGRES_DB=bf_control \
  -e POSTGRES_PASSWORD=bflocal -p 127.0.0.1:55440:5432 \
  docker.io/library/postgres:16.13
export BROWNFIELD_CONTROL_DSN='host=127.0.0.1 port=55440 dbname=bf_control user=postgres password=bflocal'
export BROWNFIELD_CONTROL_NPGSQL='Host=127.0.0.1;Port=55440;Database=bf_control;Username=postgres;Password=bflocal;Pooling=false'
python3 lab/brownfield/journal/test_journal.py
podman rm -f bf-control-pg
```

**WARNING:** The test drops the `legacy`, `brownfield` and `controller`
schemas in explicitly named disposable databases. It is not a migration tool
for existing data. Original CI retains source hashes, environment, image
digests, process signal/exit observations and `c2-summary.json`.

## Fault and negative-control matrix

- Existing gateway exits after admission, before send and after remote COMMIT;
  lost ACK recovery with exactly one decision, two postings and one outbox.
- Concurrent same-ID requests and changed-fingerprint conflicts.
- Independent parent `SIGKILL` after durable transition preparation and after
  candidate authority COMMIT. Both frozen adapters must reject writes.
- Restart recovery, stale-epoch replay, unexpected authority and missing
  outbox. Corruption must prevent thawing; repairing the disposable fixture
  does not approve a real migration.
- Both adapters refuse environment opt-out after SQL enrollment; missing or
  unreachable controller refuses new commands.
- A balanced, deliberately unjournaled privileged raw-SQL posting must still
  fail the journal audit. Monetary conservation alone cannot approve cutover.

[Original follow-up CI evidence](../../../evidence/runs/BROWNFIELD-C2-RECOVERY.md)
records 19 passing controls, exact source hashes, the unchanged ZIP and the
first failed concurrency run. Later source SHAs still require their own CI. The final negative audit intentionally fails for two unresolved
admissions and one raw-SQL bypass; the test passes only if these are detected.
No in-flight controller-partition proof, independent physical hosts, external
payment effects, WAN, RTO/RPO, capacity benchmark or owner approval is claimed.
