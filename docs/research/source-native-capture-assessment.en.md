# Source-native change capture is a product and writer-path contract, not a COBOL feature

**Issue #58 · research/assessment dated 4 November 2026 · no native source execution.** [Español](source-native-capture-assessment.es.md) · [W01 synthetic proof](../../evidence/runs/W01-SOURCE-JOURNAL.md) · [Executable interview intake](../../lab/brownfield/source_capture/README.md).

## Follow-up: synthetic snapshot-to-tail continuity oracle

The [ES](source-capture-handoff.es.md) / [EN](source-capture-handoff.en.md) follow-up now defines a **separate offline synthetic commit-history oracle** with 26 planned negative/positive tests for snapshot cut, bookmark, tail ordering and target replay. It is not a source-native CDC run and does not change the seven-family intake results or bank gates.

## Decision

**Do not automatically carry the W01 synthetic PostgreSQL journal to a customer's mainframe.** W01 proved 22/22 narrow source/target PostgreSQL controls with a journal written by a *test actor* in the same financial transaction, but has never run a Db2, VSAM, IMS, IBM i or Fujitsu capture reader. Real source-system transaction order, initial snapshot position, recovery, batch access and external money effects must be independently discovered before choosing CDC, an approved transactional outbox, a verified export or keeping the original source authoritative.

Even if an installed vendor CDC product emits every row modification, **row CDC does not prove a complete banking business event**. Cash dispensing, external clearing messages, channel acknowledgements, a temporarily offline branch, a maintenance utility and an end-of-day adjustment can cross the database's UOR. Capture and source-writer fencing are different controls.

## Product-specific capture options and traps

| Installed source path to identify | Documentation-supported *candidate*, not a deployment claim | Mandatory counterexample / owner verification |
| --- | --- | --- |
| **Db2 for z/OS 13** | A compatible replication product may read an expanded recovery log; IBM documents `DATA CAPTURE CHANGES` and Q Capture from Db2 logs with MQ delivery | List **every** table, LOB/XML limitation, catalog and tool version; prove CDC logging, Db2 data-sharing order, utility LOAD/REORG paths, retention, transaction commits and reverse/rollback handling |
| **VSAM accessed under CICS** | Classic CDC uses VSAM replication log streams, with `IDCAMS LOGREPLICATE` and `LOGSTREAMID` under applicable deployment | Prove CICS region/resource/logstream mappings, RLS vs non-RLS, recoverable access, replicated load-mode behavior and all exceptional writers |
| **VSAM batch outside CICS, non-RLS** | IBM describes CICS VSAM Recovery (CICS VR) log capture for batch non-RLS paths | JCL direct/open, utility LOAD, out-of-CICS writes, checkpoint/restores and missing histories must be accounted for; do not infer this is covered by the CICS online log |
| **IMS online** | Classic CDC can read participating IMS online/archive logs and UOR sync points | Verify installed IMS database types, DBD capture EXIT configuration, RECON, OLDS and archive coverage, DB/DC/DBCTL registration and ordering when several subsystems participate |
| **IMS DL/I batch** | Conditional Classic CDC log capture | Verify `DBRC=Y`, `DFSFLGX0` and persistent `IEFRDER`; some DL/I batch logs are unavailable until the *job step closes*, potentially causing hours of delay |
| **IBM i on Power** | Database journaling and journal receivers, including remote receivers where configured | Identify journaled physical files, BEFORE/AFTER image options, journal/receiver chain continuity, filtering, receiver deletion, commitment control and native job/utility writers |
| **Fujitsu GS21/BS2000, NEC ACOS, Hitachi VOS, Unisys or other** | **Undetermined in this increment** (do not borrow IBM terminology) | Require vendor/OS/DB/version and primary technical references plus an installation-specific native recovery test before naming any equivalent capture mechanism |

**Primary documentation consulted (not vendor installation verification):**

- IBM [Db2 13 change capture and log limits](https://www.ibm.com/docs/en/db2-for-zos/13.0.0?topic=tables-altering-table-capture-changed-data); [Q Capture / Q Apply](https://www.ibm.com/docs/en/idr/11.4.0?topic=zos-replication-event-publishing-programs).
- IBM [VSAM CDC FAQs and writer differences](https://www.ibm.com/docs/en/idr/11.4.0?topic=zos-frequently-asked-questions); [LOGREPLICATE and LOGSTREAMID](https://www.ibm.com/docs/en/idr/11.4.0?topic=replication-augmenting-vsam-data-sets-change-data-capture).
- IBM [IMS prerequisites and DL/I batch restrictions](https://www.ibm.com/docs/en/idr/11.4.0?topic=architect-system-requirements-ims); [IMS log capture and latency](https://www.ibm.com/docs/en/idr/11.4.0?topic=processing-reading-ims-logs); [DBD capture EXIT](https://www.ibm.com/docs/en/idr/11.4.0?topic=information-augmenting-downloading-dbds-ims-change-data-capture).
- IBM [IBM i journal receiver semantics](https://www.ibm.com/docs/en/i/7.6.0?topic=database-journal-management-distributed-relational-databases); [remote journal receivers and filtering](https://www.ibm.com/docs/en/i/7.5.0?topic=concepts-journal-receivers-associated-remote-journal).

The citations refer to **documentation versions**, not an installed, licensed or supported configuration for 2026. For some IBM products, version-specific restrictions and prerequisites can differ. No Fujitsu-native CDC support statement is made here: the relevant signed/versioned primary product documentation remains unverified. Historical availability, end-of-support or licensing must be confirmed by vendor/customer.

## Owner interview → observable experiment

The [machine-readable catalog](../../lab/brownfield/source_capture/capture_catalog.json) captures the official references and explicit blind spots; the [sample intake](../../lab/brownfield/source_capture/intake.example.json) intentionally marks all **seven** families `UNKNOWN`. It is not a form of customer approvals. Interview with the *application owner*, DBA, CICS/IMS administrator, batch scheduler, storage/log/DR operator, security, payment/external network owner and an independent financial reconciliation owner, separately.

For each applicable family, record evidence pointers for:

1. **Commit unit and source watermark:** Which component assigns the ordered transaction/commit position? Is it global, per subsystem, dataset, journal receiver, queue or key? A timestamp or journal row counter is **not automatically** a total committed order.
2. **Snapshot ↔ log rendezvous:** Under what named lock, consistent point or product protocol can a source snapshot be paired with the first *subsequent* captured COMMIT? Reject both missing and duplicate boundary transactions.
3. **Restart and retention:** Restart bookmarks, log/archive/receiver aging, offline and DL/I batch pauses, rollback, rebuild, schema changes and a deliberately missing log segment. Recover only under a preregistered plan; never skip to latest.
4. **Writer completeness:** CICS/IMS online, JCL batch, utilities/bulk load, channels/ATM, offline branches, asynchronous replay, elevated repair jobs and external effects. A single-source CDC connector may capture **less than all financially meaningful writes**.
5. **Independent reconciliation:** Compare accepted transaction IDs, paired postings, funds invariants, source account versions, external payment/cash effects and UNKNOWN outcomes, not just row counts.
6. **Owner-controlled safety:** Source-enforced writer fencing and measured switch/rollback during an actual fault; log-based capture does not become new financial write authority by itself.

**Fail-closed outcomes:** `RETAIN_SOURCE`, `CONDITIONALLY_DESIGN`, `INCONCLUSIVE`, or `READY_FOR_EXTERNAL_REVIEW`. No automatic `MOVE_LEDGER` or bank PASS exists. If source logs are inaccessible or incomplete, an explicitly approved read-only shadow/export plus full reconciliation might still be valuable; do not promise near-real-time guarantees or authoritatively process payments.

## What this increment proves — and does not

The new source-capture gate tests **only intake structural consistency and refusal of self-asserted approvals**. Its synthetic fake refs can make it return `READY_FOR_INDEPENDENT_REVIEW`, and the tool explicitly reports `evidenceBytesVerified=false` and `nativeCaptureTestExecuted=false`. Passing its unit tests does **not** mean any native vendor system ran or that any referenced evidence exists. The only executed W01 journal proof remains the separate two-PostgreSQL 22-case laboratory.

The real [source-side fence protocol](../BROWNFIELD_SOURCE_FENCE.md) and [issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58) remain open for owner-provided independent acceptance. **TODM G2 `INCONCLUSIVE`, G6 `BLOCK`**. E2 stays `partially_verified`, issue #8 administratively closed, #32 completed for methodology, #53 frozen. No release is authorized.
