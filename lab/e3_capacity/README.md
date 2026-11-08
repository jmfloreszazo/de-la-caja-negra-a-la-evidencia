# E3 exploratory synthetic process-failure harness

**EXPLORATORY, not E3 capacity acceptance.** This executable offers real transfers
against the existing .NET `PgLedger` and PostgreSQL E1 schema. It does not fill or
approve `lab/performance-contract.json`. There is no invented production workload,
mainframe baseline, price, TLS, external authentication, managed SQL deployment,
or distributed high-availability claim.

Topology: **SINGLE_HOST_PROCESS_FAILURE_NOT_PHYSICAL_HA**. Two separately identified
service processes share one disposable loopback PostgreSQL database. Replica 0 is
killed and restarted; replica 1 remains running. Routing does not switch or retry.
A service-process loss is not host, database, disk, replica or physical-node loss.
The same local executable can run on an Azure VM; that does not make its output an
Azure capacity result. This harness never provisions or contacts Azure.

## Safety and prerequisites

- .NET 10 SDK, Python 3.10+ and the existing `lab/e1_pg/requirements.txt` dependencies.
- An existing **disposable** E1 PostgreSQL fixture reachable at `127.0.0.1` only.
  `E1_PG_DSN` and `E1_PG_NPGSQL` must explicitly identify the same database, user,
  port and loopback host. Do not use production credentials. The PostgreSQL user
  needs schema creation privileges. Options/search-path overrides are rejected.
- Set `E3_DISPOSABLE_FIXTURE=YES` explicitly. Connections to administrative default
  databases (`postgres`, `template0`, `template1`) are rejected.
- The runner creates an unpredictable `e3_<uuid>` schema. E1 schema initialization
  and the negative control affect only this owned schema, never existing public
  E1 tables. It drops only its owned schema in `finally`. Concurrent experiments
  must still be considered a confounder for timing; isolation is not dedicated CPU.
- Services bind only IPv4 loopback on dynamically selected ports. PID/schema health
  responses prevent accidentally measuring an unrelated listener. No existing
  services or containers are killed. Child process handles are retained for cleanup.

## Run

From the repository root, with the launcher's E1 connection variables already set:

```powershell
$env:E3_DISPOSABLE_FIXTURE = 'YES'
python lab\e3_capacity\test_e3.py --profile smoke --output lab\e3_capacity\results\smoke-001
python lab\e3_capacity\test_e3.py --output lab\e3_capacity\results\default-001
```

Output must be a **new** directory within the repository. The default output is a
unique ignored directory under this project. The runner builds its fixture unless
`--skip-build` is provided after an explicit successful build:

```powershell
dotnet build lab\e3_capacity\E3Fixture\E3Fixture.csproj -c Release -m:1 --disable-build-servers
python -m unittest discover -s lab\e3_capacity -p test_harness.py -v
python lab\e3_capacity\test_e3.py --profile smoke --skip-build --output lab\e3_capacity\results\smoke-002
```

The new fixture references DurableRpc without changing M2's service, HTTP/2,
benchmark, protocol, or closed-loop defaults. E3 deliberately uses HTTP/1.1 REST
with Python's standard library; it is not a transport comparison with M2.

## Preregistered workload and observation semantics

`workload.json` fixes two selectable profiles before execution:

| Profile | Rates (offers/s) | Phase length | Total offers | Kill / restart |
|---|---|---|---|---|
| default | 20, 40, 60 | 6 seconds each | 720 | 8 / 10 seconds |
| smoke | 10, 20, 30 | 2 seconds each | 120 | 2.5 / 3.5 seconds |

All identities and scheduled times are materialized before services start. Rates
never adapt to completions. Scheduling uses a monotonic clock and absolute intended
send times. At most 32 requests can be in flight. Rather than wait for a permit and
disguise a closed-loop workload, the scheduler records a missed offer when full or
more than 100 ms late. Worker dispatch rechecks lateness. HTTP calls have 2-second
timeouts. Build (90 seconds), readiness, SQL statements and process cleanup are
bounded; normal defaults take well under three minutes with dependencies available.

Every offer remains in the record: acknowledged commit/rejection, missed schedule,
in-flight limit, connection refusal, ambiguous HTTP/transport/response, or an
aborted-run offer. No retry hides a failed/ambiguous outcome. End-to-end latency is
completion minus **scheduled**, not actual, send time. Missed offers have no fake
zero latency. ACK-only percentiles explicitly exclude non-ACK outcomes and cannot
be interpreted as a whole-population SLA. `clientDrainSeconds` is only completion
of issued client requests, not a production backlog-drain or RTO measurement.

After stopping writers, bounded backend quiescence precedes a read-only SQL
snapshot. Independent E1 `oracle.py` is loaded unchanged and reads persisted state.
Reconciliation joins **every operation ID and payload**, checks acknowledged results,
records committed-but-unacknowledged operations and absent outcomes, and rejects
unexpected persisted identities. The accounting oracle checks double entry,
conservation, projection and outbox atomicity. A separate negative control removes
one posting, demands oracle rejection, restores it, and demands clean verification.
The snapshot is captured before corruption. Recovery requires an acknowledged
transfer through the restarted service, not merely a health response.

## Artifacts and result interpretation

- `workload.json`: complete fixed profiles and limitations; selected profile in summary.
- `offers-planned.json`: all planned identities, routing, amounts and intended times.
- `offers.json`: every outcome, actual dispatch/completion, scheduled-time latency,
  response/error class and independently persisted status.
- `ledger-snapshot.json`: independently read accounts, operations, postings, outbox, duty.
- `summary.json`: process IDs, kill/restart/recovery times, outcomes, reconciliation,
  oracle and negative-control results, binary/source/artifact hashes and limitations.
- `host.json`: OS/kernel, machine, node, CPU count, Python and available UID/GID.
- `dotnet-info.txt`, `build.log` and `service-*.log`: runtime, bounded-run build and owned service output.
- Runtime `*.dll` and `*.json` files copied directly from
  `E3Fixture/bin/Release/net10.0` into the output directory before execution. Their
  unchanged basenames occur in both `runtimeArtifactSha256` and `artifactSha256`.
  Retention rejects links, non-files, overwrites, more than 128 files or 128 MiB.
  Source and retained bytes are hash-compared; no rebuild substitutes for evidence.

The summary also records PostgreSQL version and actual durability settings
(`fsync`, `synchronous_commit`, `full_page_writes`) without treating them as proof
of replicated durability. Per-phase outcomes remain separate from the aggregate.

Source files are hashed even for dirty/exported workspaces. Optional
`SOURCE_HEAD_SHA`, `SOURCE_ARCHIVE_SHA256`, `SOURCE_WORKTREE_DIRTY` must be supplied
together (40/64 hexadecimal characters and `true/false/0/1`). They are recorded as
**launcher-attested export metadata**, not proof of execution location. Local Git
head/status are recorded separately; host/source hashes do not authenticate a host.
Connection strings and passwords are never written to artifacts.

Exit 0 requires `status == "EXPLORATORY_COMPLETED"` **and** `errors == []`: this run
completed its bounded checks, not a capacity PASS. The status is assigned before
cleanup; a cleanup error can leave that status unchanged while the exit code is
nonzero. Never accept the status field alone. Expected failed or missed offers do
not themselves prevent exploratory completion; this is not an all-requests-success
or SLA verdict. Nonzero exits retain partial offers and an error/check-failure
summary when artifact initialization succeeded. Inspect errors, cleanup flags, all
offers and process logs; do not promote incomplete or failed observations into
acceptance.

The owned schema is dropped before the launcher can take its final PostgreSQL
dump. That dump does **not** retain this run's private E3 ledger. The pre-corruption
`ledger-snapshot.json` is the retained logical ledger observation; it is not a
PostgreSQL backup, WAL capture or restore test. Keep it with its hash and the full
archive. Source hashes must be compared with the run's exported source, not later
working-tree edits (including documentation clarifications).

### Parent archive verifier assertions

Apply these to the archived run, independently of the runtime's summary verdict:

1. Require `classification == "EXPLORATORY_SYNTHETIC_NOT_E3_CAPACITY_ACCEPTANCE"`,
   `topology == "SINGLE_HOST_PROCESS_FAILURE_NOT_PHYSICAL_HA"`,
   `capacityAcceptance is False`, `status == "EXPLORATORY_COMPLETED"`, `errors == []`,
   `schemaCleanup is True`, and `survivingServiceAliveAfterLoad is True`. Require the
   launcher's successful workload/collection/cleanup exit codes separately.
2. Verify SHA-256 of every named `artifactSha256` file, with safe relative basenames;
   require at least `host.json`, `workload.json`, `offers-planned.json`, `offers.json`,
   and `ledger-snapshot.json`. Require `hostSha256 == artifactSha256["host.json"]`.
   The summary is not self-hashed: bind it to the parent's independently recorded
   archive digest. Check export metadata against that archive's source attestation.
   Require every `runtimeArtifactSha256` entry to have matching retained bytes and
   an identical `artifactSha256` entry; `binarySha256` must equal the retained
   `E3Fixture.dll` hash. Earlier runs such as `e3-azure-20261108-01` predate byte
   retention: retrieve their original build output, verify its recorded hashes,
   and preserve it as separately identified supplemental evidence without changing
   original reports. If unavailable, report the gap; a rebuild is not a substitute.
3. For `profile == "default"`, require rates `[20, 40, 60]`, six-second phases,
   720 unique planned and final offer identities, phase sizes `[120, 240, 360]`,
   `measurement.offered == 720`, and `nominalOfferWindowSeconds == 18`. Preserve
   each planned identity, index, phase, rate, source, destination, amount, replica,
   and scheduled time in the final record. Recompute absolute phase schedules,
   routing `index % 2`, ring accounts and amounts from the archived workload.
4. Recount final outcomes and phase outcomes exactly; their sums must equal offer
   counts, with no `MISSED_RUN_ABORTED`. Require dispatched completion timestamps
   and `endToEndMs == 1000 * (completionSeconds - scheduledSeconds)` within floating
   tolerance. Missed offers have no dispatch/completion or invented zero latency.
   Recompute ACK-only p99 separately; do not apply it to non-ACK offers.
5. Join snapshot operations to final offers by unique operation ID and exact
   `(src, dst, amount)`; reject unknown identities. ACK commits/rejections must have
   their matching persisted status. Missed/connection-refused offers must be absent.
   Preserve ambiguous outcomes even when independently persisted. Recompute
   `reconciliation.persistedOperations`, `persistedCommits`, and
   `unacknowledgedPersistedCommits`; require `consistent is True`, `problems == []`,
   and matching per-offer `persistedStatus` rather than trusting summary counts.
6. Independently check the snapshot: accounts 1–16; nonnegative balances summing to
   1,600,000; initial 100,000 plus postings equals each balance; every committed
   operation has exactly its source debit and destination credit, with zero sum;
   rejected operations have no postings; every commit has exactly one
   `TransferCommitted` outbox event; no orphan/duplicate posting or outbox keys.
   Require all seven explicitly named E1 checks to exist and be `True` in
   `oracleBefore`, `oracleAfter`, and `negativeControl.restoredOracle` (not vacuous
   `all({}.values())`). Require `negativeControl.detected` to contain at least
   `twoPostingsPerCommit` and `projectionAgrees`. The clean snapshot alone cannot
   independently prove that transient corruption/restoration was executed.
7. Require ordered `KILL_PROCESS`, `RESTART_PROCESS`, `RECOVERY_HEALTHY` events for
   replica 0: killed PID equals `initialPids["0"]`; restarted/recovered PID matches
   and differs from both initial PIDs; scheduled kill/restart are 8/10 seconds;
   actual times are ordered and not earlier than intended. All three owned PIDs
   must have non-null terminal exit codes (not necessarily zero: Linux SIGKILL is
   `-9`). Require `recovery.healthySeconds` to match the health event and independently
   find a replica-0 `ACK_COMMITTED` with dispatch at/after that event, alongside
   `recovery.recoveredServiceAcknowledgedCommit is True`.

For the specific `e3-azure-20261108-01` archive, additionally require outcomes
`{"ACK_COMMITTED": 668, "FAILED_CONNECT": 48, "MISSED_SCHEDULE": 4}`, 668 persisted
commits/operations, zero unacknowledged persisted commits, 1,336 postings, 668 outbox
rows, and per-phase commits `[120, 192, 356]`. These are observations of that run,
not acceptance thresholds for future executions. Azure execution location comes
from the parent deployment/run evidence, not the harness's classification or hashes.
The E3 protocol still requires a real approved contract, external environments,
physical-unit-loss coverage, workload parity, and independently established cost.
