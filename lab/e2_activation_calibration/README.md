# E2 observer positive calibration

Status: original run #41630777280 observed the sensitive negative and live positive control.
See the [paired evidence account](../../evidence/runs/E2-ACTIVATION-CALIBRATION.md).
This is diagnostic-worker calibration; ordinary-grain partition concurrency remains open.
Depends on the observer in PR #78. Software and developer documentation are English.

## Question and fixed acceptance

Can the incoming-call observer detect two **actual Orleans activation IDs**
servicing the same diagnostic grain key while their request envelopes overlap?
Do conflicting commands still produce exactly one durable effect through the
unchanged PostgreSQL ledger?

The separate diagnostic grain uses `[StatelessWorker(maxLocalWorkers: 2)]`.
Multiple activations are explicitly allowed in this grain type. A bounded
asynchronous barrier before the ledger keeps the first request busy until the
second enters. No `[Reentrant]`, default-policy change, ledger change or fake
activation ID is used. The first two commands share an operation ID but differ
in amount (31/37 cents). One must COMMIT and the other return ID_CONFLICT.
Replay must return DUPLICATE_COMMITTED; changed payload must return ID_CONFLICT.
The SQL oracle must observe exactly 1 operation / 2 postings / 1 outbox and 7/7 invariants.

Before that positive case, a **fresh process and reset database** run a single
request. Its two-party barrier must time out before the ledger is called.
Require zero operations, postings and outbox with 7/7 invariants. The observer
must record BEGIN/ERROR and no overlap. A silently disabled observer fails both
acceptance checks.

Record full stdout/stderr, actual activation IDs, process/session and monotonic
clock metadata, exact Git source/checkout and source hashes, SQL snapshots,
runtime/package/container provenance and all original failures. Positive
acceptance requires an actual overlap between the first two conflicting
commands, distinct activation IDs and the same grain ID; a generic positive
status, concurrent client submission or a catalog row is insufficient.
The classifier is also tested with missing, forged and non-overlapping witnesses.

## Scope boundary

This calibrates the detector and exercises SQL authority with deliberately
multiple **diagnostic stateless workers on one local silo/host**. It does not
demonstrate concurrent ordinary AccountGrain activations, a C05 partition,
natural split brain, physical HA, capacity or bank acceptance. No whole E2 gate
is closed. The accepted AccountGrain, its placement policy, old observer,
historical ZIPs and all financial/oracle sources remain unchanged.

Microsoft documents this deliberately multi-activation worker behavior:
[stateless worker grains](https://learn.microsoft.com/en-us/dotnet/orleans/grains/stateless-worker-grains).
It is used here as a test control, not as a recommendation to store account
authority in worker-local state. A subsequent ordinary-grain partition trial
still needs its own independently observed activation identities and SQL oracle.

## Reproduction

The dedicated GitHub Actions job starts disposable PostgreSQL 16.13 on fixed
loopback port 55438, publishes the separate host and runs the negative then
positive case with explicit opt-ins. It runs the language and paired-book
checks before execution. Original artifacts are uploaded even on failure.
No book finding, release/tag or claim status is promoted by preparing this source.
