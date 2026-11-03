# E2 incoming Transfer invocation observation

Issue #24. **New experiment; no original execution accepted yet.**
This project references the unmodified `AccountGrain` and `PgDurableLedger`.
Its separate host reproduces the fixed ADO.NET private fixture and adds one
incoming-call filter. The original host and historical auditors remain intact.
The host duplication is test scaffolding; future fixture changes must review
both configurations. Logging changes timing, so results describe this observer
host, not a retrospective interpretation of earlier runs.

## Fixed protocol before execution

Reuse the 120-second schedule and sampled recovery in the
[long protocol](../e2_orleans/LONG_PARTITION_PROTOCOL.md), including all SQL,
packet, liveness and assisted-recovery gates. The runner adapter replaces only
the silo executable. Original external clients, placement seeding, fault rules,
ledger and seven independent SQL invariants remain unchanged. Two fresh CI
jobs test opposite directions on one physical host each.

For every incoming `Transfer`, record BEGIN and END/ERROR with the Orleans
activation ID, grain ID, call ID, process session, per-process sequence,
payload, result, UTC, monotonic timestamp/frequency, kernel boot ID and Linux
time namespace. No extra grain RPC, placement policy, delay or retry is added.
Full stdout is retained and hashed **before each old/new silo is removed**;
the original harness's truncated diagnostic tail is not the source of truth.

Fail on malformed events, gaps, duplicate/orphan ends, identity changes,
backward ticks, missing observer readiness in any silo generation or an ACK
without a compatible observed completion. Reconcile every successful filter
result with the final SQL payload, status, operation/posting/outbox cardinality
and all seven independent invariants. An ERROR or missing END never proves
rollback. Abrupt process exit can leave incomplete request envelopes; retain
them explicitly rather than converting them to completed intervals.
Idle generations can have no Transfer events; readiness is not financial
coverage. At least one completed call and every acknowledged payload/result
must be present in the retained log set.

Compare only complete request envelopes for the same grain and distinct
activation/session identities with identical boot ID, time namespace and clock
frequency. Strictly positive interval intersection is recorded as
`OVERLAPPING_REQUEST_ENVELOPES_OBSERVED`. It encloses filter/logging/scheduling
overhead; it is **not** a measurement of simultaneous CPU execution, overlapping
SQL transactions or entire activation lifetimes. Non-comparable clocks and
incomplete calls limit coverage. No forced duplicate activations are introduced.

`PASS_OBSERVATION_ONLY` means the existing schedule gates, observer integrity
and SQL/ACK reconciliation passed. It does not require a positive overlap and
never establishes exclusive activations, absence of split brain, physical HA,
production RTO/RPO, sustained capacity or bank approval. If no overlap appears,
the positive concurrent-activation question remains open. E2 stays partial.

## Reproduction

Run negative interpretation controls without .NET, SQL or Podman:

```bash
python3 -m unittest discover -s lab/e2_activation_observer -p 'test_observation.py' -v
```

The dedicated CI workflow publishes both executables into the fixture app
directory, records exact source/checkout, source hashes, runtime and images,
then runs `run_observation.py` with explicit disposable-fixture opt-ins. All
original reports, full logs, PCAPs and FAIL outcomes are uploaded. Independent
artifact/source audit is required before a paired ES/EN evidence account or
any claim change. Existing evidence, release IDs and frozen #53 are unchanged.
