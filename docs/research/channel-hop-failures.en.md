# Isolating failures by banking channel hop

**5 November 2026 · #30 · source-neutral synthetic trace only.** [Español](channel-hop-failures.es.md) · [Existing ATM channel contract](../../lab/channels/CONTRACT.md) · [Previous late-advice experiment](channel-late-advice.en.md).

## Why a generic "network timeout" is not an acceptance result

An ATM, the ATM/EFT switch, the issuer/processor and the core may be independent systems. A lost request **before** the switch, a lost request **between** switch and core, and a lost response **after** an issuer commit expose different states. A client timeout does not establish that a CICS unit of work (UOW) committed or rolled back. IBM documents that CICS SYNCPOINT commits updates to **recoverable resources in that UOW**; a task may comprise more than one UOW. It does **not** roll back physical cash or a third-party response. [IBM CICS syncpoints](https://www.ibm.com/docs/en/cics-ts/6.x?topic=work-synchronization-points) · [CICS UOW recovery](https://www.ibm.com/docs/en/cics-ts/6.x?topic=processing-unit-work-recovery).

Microsoft's [transient fault guidance](https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults) recommends explicit timeouts and bounded retry/backoff. In a financial command with an ambiguous commit outcome, however, a **new operation ID** is not a harmless retry. Use a durable original operation identity and query the **authoritative owner** for its decision before changing state, under the actual bank's approved policy. Backoff alone does not provide end-to-end exactly once.

Visa's [June 2024 ATM nonreceipt/partial-cash dispute guidance](https://usa.visa.com/dam/VCOM/global/support-legal/documents/merchants-dispute-management-guidelines.pdf) distinguishes original cash-disbursement evidence from evidence of a credit or reversal. In a withdrawal, do not infer cash success from the switch's advice or authorization response alone; physical-device evidence and accounting are **separate observations**.

## Seven predeclared logical fault traces

| Case | Failed/delayed boundary | What the synthetic trace supports | What must not be inferred |
| --- | --- | --- | --- |
| H01 | ATM→switch: request is lost before delivery | `NO_CORE_AUTHORIZATION_EVIDENCE` | Not a proven decline or physical success |
| H02 | Switch→core: original request dropped | `NO_CORE_AUTHORIZATION_EVIDENCE` | No authorized offline cash fallback |
| H03 | Core COMMIT followed by lost core→switch reply; link restored | `AUTHORIZATION_RECOVERED_BY_STATUS` | A proven authorization is **not** proof of cash delivery |
| H04 | Core approves, device command dispatched, ATM↔switch fails | `CASH_UNKNOWN_NO_REDISPENSE` | A late advice is not a final physical journal |
| H05 | Writer ownership changes; old issuer reply arrives afterward | `QUARANTINED_OLD_OWNER_REPLY` | An old reply cannot establish a new-owner transaction or enable dual writes |
| H06 | Device journal says 6,000 of 10,000 delivered, ledger matches | `PARTIAL_CASH_RECONCILED_SYNTHETICALLY` | This fictional match is not authenticated physical evidence |
| H07 | Switch cannot reach core and asks to use stand-in without delegation | `STAND_IN_DENIED` | The channel cannot invent spending authority |

The [English-only synthetic trace fixture](../../lab/channels/network_fault_fixture.json) contains declared event sequences on **two named logical links**, `ATM_SWITCH` and `SWITCH_CORE`, plus `DEVICE`, `ISSUER` and `CONTROL`. Each observation has an ordered step and a source epoch. The [strict trace oracle](../../lab/channels/network_fault_gate.py) compares these with separately declared issuer decisions, device states/journal IDs, posted amounts and active writer epoch. A false delivery during a down link, an issuer COMMIT without a source request, a status response without the original COMMIT, duplicate device command, posting before final journal, a stale owner event, and a purported stand-in approval are rejected.

A **route change is not proof of source fencing**. The old epoch reply is quarantined in the fictional fixture; a real migration still requires an incumbent-owned fence and full online, batch, offline and privileged writer coverage per [the source-fence method](../BROWNFIELD_SOURCE_FENCE.md). The oracle never promotes an event or writes to a core, switch or device; nor does its status query authenticate an issuer.

## What actually ran, what still must run

The 40 Python controls and seven traces are designed for an exact-SHA CI workflow. The status `PASS_SYNTHETIC_HOP_CONSISTENCY` means **internal agreement of fictional trace and snapshots only**. It is possible to fabricate a coherent source decision and a coherent channel trace; they would pass without any authentic bank evidence. No real TCP connection is severed, no physical network hop is partitioned, no dual-host failure domain or live ATM/switch/issuer is accessed, and no source log or real device journal is independently authenticated. The existing .NET 10 + two PostgreSQL Podman channel lab and its previous original CI are **separate evidence**, not claims by this new trace evaluator.

To make this representative of a customer, obtain an authorized topology and a separate timing budget for **ATM/device↔switch**, **switch↔issuer/core** and **core↔writer/data**. Introduce and record *real* drop/delay/duplicate/reorder failures per hop, on disposable isolated endpoints, with synchronized trace identity; collect independent issuer COMMIT/UOW/journal, actual device deliver/reject/retract/cash-stock, switch-message correlation, and downstream posting/dispute outcomes. Prove stable operation identity and owner fences through recovery and cutover; test late responses after authority change and retention windows. Consent, network certification, PCI/HSM and bank authorization are **not** replaced by this experiment.

**Safety claim on every output:** `physicalLinkCutTested=false`, `automaticAuthorizationAllowed=false`, `automaticDispenseAllowed=false`, `automaticPostingAllowed=false`, `automaticReversalAllowed=false`, `cohortWriterCutoverAuthorized=false`, `productionApproved=false`; TODM **G2 INCONCLUSIVE / G6 BLOCK**. E2 remains `partially_verified`. #30 stays open, #53 frozen. No new release or bank cutover from this increment.
