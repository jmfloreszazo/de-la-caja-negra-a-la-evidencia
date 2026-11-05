# Synthetic channel contract V1

Status: preregistered design until an original native/SQL campaign and independent audit exist. Tracks #30, including the retained #29 checklist. This is a new bounded example, not an approved bank policy or a copy of CICS semantics.

## Roles and stores

Two disposable PostgreSQL 16.13 instances run on one Linux host. The core stores accounts, holds, operation decisions, paired postings and financial outbox. A separate simulated device store owns immutable command outcomes and its own cash-stock counter. A native .NET 10 HTTP API writes only the core; the Python device adapter writes the device store. A read-only Python oracle reads both independently. Shared host and fixture credentials do not establish security/failure-domain isolation or physical hardware guarantees.

Amounts are integer cents in one fictional currency. Customer accounts 1/2 start at 10,000 each; a synthetic cash-control account 3 starts at zero. A posted withdrawal transfers the actual dispensed amount to that control account. This closed-world teaching ledger is not a bank-approved chart of accounts, authorization/settlement policy, PCI/EMV implementation or real ATM protocol.

## Contract decisions

1. An operation ID binds kind, channel, source, target, requested amount and terminal. A conflicting reuse is rejected. Diagnostic faults and retries do not change the financial identity or extend the first expiry.
2. Authorization reserves funds under the source-account lock. Available funds equal recorded balance less active holds; both digital transfers and cash authorizations use that rule. Account locks follow ascending ID order.
3. Before device execution, the core durably records a stable device command and `DISPENSE_PENDING`. Its public outcome is UNKNOWN. Reusing that command is deduplicated by this simulated device; real hardware needs an independently established equivalent capability.
4. Device inventory change and its final command row share one device-DB transaction. This is an explicit emulator assumption, not atomicity between physical cash and a database. The core transaction cannot undo the device row.
5. Reconciliation reads a final immutable device row. A missing record is UNKNOWN, never zero cash or a rollback. A full/partial positive amount posts exactly that amount once, releases the whole hold and writes two postings plus one financial outbox row atomically. A final zero result cancels and releases without financial postings.
6. Expiry releases only an AUTHORIZED, undispatched hold. A pending device action cannot be auto-expired or replayed under a new command ID. Manual repair for real hardware/journal discrepancies is outside the automated policy.
7. A digital transfer commits its decision, balances, postings and outbox in one core transaction. A lost HTTP response remains client UNKNOWN until an authoritative status query; it does not justify another debit.
8. No approved stand-in delegation exists in this fixture. Core unavailability never authorizes offline cash. Real stand-in budgets, issuer rules, device proof/authentication and source-side migration fencing remain unimplemented.

## Additional bounded offline late-advice correlation, NOT a new native financial engine

The separate [`advice_gate.py`](advice_gate.py) and [`advice_fixture.json`](advice_fixture.json) are fictional observations used to exercise the **#30 L09/E09** correlation and denied stand-in boundary. This does not extend the two SQL stores' physical-device simulation, no live scheme network runs, and does not change the original 10-case/7-oracle native evidence. The outcome of a network advice/reversal is not itself permission to post, reverse or dispense, and identical network delivery duplicates must not create another financial identity. A reused STAN-like field cannot be assumed globally unique across terminals; the durable operation ID remains separate.

When the device journal is UNKNOWN, no arrived advice can infer cash. A full reversal requested after partial cash is delivered must be adjudicated against a trusted device journal and issuer policy, not automatically executed. Stand-in without approved owner delegation is DENIED. The new gate always retains G2 INCONCLUSIVE and G6 BLOCK.

## Additional independent logical-hop fault contract (synthetic only)

The [per-hop trace oracle](network_fault_gate.py) and its [seven synthetic traces](network_fault_fixture.json) ask which hop is unavailable: ATM→switch, switch→core, or a reply after issuer COMMIT. Other cases test an UNKNOWN dispense journal, a stale response after writer-epoch change, a partial cash amount and an undelegated stand-in attempt. **Forty adversarial tests** reject impossible delivery during a failed link, false issuer COMMIT/status, duplicate dispense/posting, fabricated owner epochs, stale replies crossing authority, and invented bank approvals.

The experiment **only replays fictional JSON**, rather than cutting a real Ethernet/TCP path. The original owner controls financial authority and recovery. A timeout is never a bank decline or success by itself; core approval is not physical dispense; a missing physical journal remains UNKNOWN; old-owner responses after a route change are quarantined without allowing new authority. All outputs are marked `physicalLinkCutTested=false` and `cohortWriterCutoverAuthorized=false`, G2 INCONCLUSIVE/G6 BLOCK.

The original .NET/Podman/two-PostgreSQL channel experiment and archived evidence are unchanged. Extend #30 with actual isolated per-hop transport tests, issuer-approved negative controls and signed device/ledger witnesses; no synthetic event proves production fencing.

## Actual loopback TCP loss on the disposable native digital transfer (bounded #30)

The native channel driver includes a one-shot **real local TCP proxy** to the already running .NET 10 `POST /transfer` route. This is deliberately different from the earlier **fictional** H01–H07 hop-event protocol: socket accept, reset, upstream HTTP 200, delayed reply and client timeout are observed in a live single-host environment, while an independent Python/SQL oracle checks the financial database.

The three cases are named `tcp-drop-before-forward`, `tcp-drop-after-owner-response` and `tcp-delay-owner-response`. In the first case the proxy never opens an upstream socket and the original SQL snapshot is empty before the same-ID first attempt. In the second and third cases the proxy actually forwards the original HTTP request, observes the owner's reply *after* the .NET `CommitAsync`, and deliberately prevents a timely client reply. A read-only snapshot confirms the original one COMMITTED operation, two postings and one outbox **before** replay. Querying the original operation ID and retrying that same identity does not create a second transfer; the seven existing independent financial checks are evaluated before/after where applicable.

This is a **synthetic business workload over real loopback sockets** only, not a separate WAN/ATM/switch or an original bank CICS/UOW. The proxy cannot forward arbitrary bank routes/hosts, cannot execute without the disposable fixture guard, and never grants any authorization or change of writer. The independent [13-case original-run validator](../../scripts/check_channel_transport.py) and its **18 evidence refusal checks** reject false claims about network partitions, bank approval or posting multiplicity. The original historic **10-case** channel experiment remains separately preserved. The new cases are digital transfers only; no physical notes are involved.

## Initial native acceptance matrix

| Case | Required observation |
| --- | --- |
| Full cash | Authorize, prepare, one device execution, POSTED actual amount; idempotent repeats |
| Zero cash | Final device zero, CANCELLED, hold released, no financial postings |
| Partial cash | Requested 6,000, device 4,000, exactly 4,000 posted and remaining hold released |
| Device response lost | Actual device commit before lost reply; core stays UNKNOWN/held until journal reconciliation; no new dispense ID |
| Core crash before settlement commit | Actual external SIGKILL after mutation barrier; core rollback, device record survives; restart reconciles once |
| Settlement response lost | Core COMMIT precedes HTTP abort; client UNKNOWN, status query/replay return one posted result |
| Digital response lost | Actual HTTP abort after COMMIT; same ID resolves without another transfer |
| ATM/mobile race | Two 6,000 requests compete for 10,000 funds; exactly one can consume/reserve, the other declines |
| Conflict and duplicate | Changed intent rejected; same intent cannot create another cash or ledger effect |
| Expiry | Undispatched expired authorization releases; pending device work remains UNKNOWN with its hold |
| Missing journal | Pending state and hold remain; no inference of zero or success |
| Oracle mutations | Reject conserved-but-double-posted cash and a false POSTED decision without postings; restore no historical observations |

Every case retains HTTP requests/responses, server/device logs and both complete SQL snapshots. Seven independent checks cover projection/nonnegative balances, conservation, intent/finality, exact paired postings, atomic financial outbox, holds/availability and device-cash reconciliation. Deliberate mutants must fail the oracle. Original FAIL/INCONCLUSIVE data remains visible; a green test matrix is only bounded synthetic functionality.

Transport encryption, identity/HSM/PIN, ISO 8583/NDC/DDC certification, clearing/settlement schemes, full physical dispense semantics, real stand-in approval, production capacity, physical HA and bank release authorization are out of scope. Remaining #30 L01–L16 clauses must be mapped individually after actual evidence; do not close #30 from this subset.
