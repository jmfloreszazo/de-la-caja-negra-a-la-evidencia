# Loopback placement observation — issue #74

Status: **original observation controls verified**, run #41601478234 on
`c547c3f34badda0cb57ab0b496917dadb1485b04`; see
[the audited paired report](../../evidence/runs/E2-PLACEMENT-OBSERVATION.md). This implements
failure-specific observability, not a default-placement fix. E2 remains
partially_verified, G2 INCONCLUSIVE/G6 BLOCK, #53 frozen, no release/tag change.

## Problem preserved

Original ADO.NET loopback run #41528813076, source
`958961906de0ca5d3945d410c64d465ba7d34a3e`, failed the strict two-host
placement prerequisite before SIGKILL. Its archive contains a legitimate earlier
development-provider success and no ADO.NET success. The provider-specific
success filenames were already separate; what was missing was the failed
provider's own map, membership, phase and raw probe outcomes. See the
[preserved ZIP and decoded log](../../evidence/runs/E2-C05-C06-DIRECTIONAL.md).

## Recorded contract

- Preserve the original 1..16 keys, strict two-PID prerequisite, wait budget,
  SIGKILL semantics, normal financial calls and SQL oracles. Retries observe
  existing keys; they do not redistribute them. Accepted C# grain, ledger and
  placement policy remain unchanged.
- Every execution has a unique ID and provider-specific fsynced JSONL journal,
  atomic manifest and, on failure, a FAIL report. Every probe attempt records
  returned PIDs, raw client stdout/stderr or timeout byte captures, real SQL
  membership (ADO.NET only), process liveness and observed silo policy/logs.
- Record accurate phases before startup, placement, each financial call,
  SIGKILL, recovery and reconciliation. Separate attempted financial commands,
  kill requested and kill confirmed. Unobservable SQL is an error observation,
  never an empty successful result.
- Keep logs alive through failure capture and copy their original bytes before
  process cleanup. Bind copied logs and journal by SHA-256. Existing successful
  files are not accepted as this execution's success: the execution manifest
  must bind the exact provider-specific file after it is newly written.
- A failure remains raised and FAIL; no continue-on-error or assertion weakening.
  Normal success filenames retain their current semantics. The shared client
  function's observer is optional so in-flight tests keep their default path.

## Preregistered real negative controls

Run two fresh Ubuntu jobs, one development and one ADO.NET, against disposable
loopback PostgreSQL 16.13 on port 55434, Orleans 10.4.0 and unchanged account
logic. Require two successful independent SQL sessions before schema work.
Record source/checkout, file hashes, SDK, actual image and runner metadata.

Use a byte-identical historical development PASS from the retained ZIP as an
explicit **old input**, not a result from this job. Trigger an opted-in
`OBSERVATION_NEGATIVE_CONTROL_AFTER_FIRST_PROBE` exception after the first
actual 1..16 identity probe and before any financial invocation or SIGKILL.
This is an induced observation failure, **not a reproduced natural one-sided
placement failure**. The parent must require child exit 1, the exact marker,
correct provider/phase, both actual running server PIDs, an independent client,
the original key map, default-policy log markers, captured raw output, exact
journal/log hashes and current-source clean-worktree metadata. For ADO.NET,
require both persisted SQL members Active. Development SQL membership is
explicitly not applicable, not fabricated.

An independent SQL observer must require zero operations/postings/outbox and
all seven invariants. The old PASS bytes must be unchanged, the new manifest
must remain FAIL and must not reference that old file as a new success.
A successful parent reports NEGATIVE_CONTROL_VERIFIED; it is not failover,
policy correctness or an accounting transfer PASS. Preserve every failed job
and original artifact before any correction.

## Remaining work

These controls verify the evidence recorder. They do not explain the original
concentration, establish exclusive activation, prove physical HA, long-partition
recovery, sustained capacity or banking acceptance. #74 remains open for natural
placement investigation or a separately scoped controlled-loopback alternative.
Publish paired ES/EN interpretation only after actual original CI and audit.
