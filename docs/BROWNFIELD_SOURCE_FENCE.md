# CAP-007/005 brownfield: proving source-side authority before cutover

**Status: engineering contract and structural intake, NOT an executed incumbent fence.** [Español](BROWNFIELD_SOURCE_FENCE.es.md) · [Issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58). The current synthetic C2 controller, legacy and candidate each have separate PostgreSQL persistence; they cooperate in an artificial authority and admission protocol. That does **not** revoke authority from a real mainframe, CICS/IMS transaction, Db2/VSAM update, batch job, offline branch, asynchronous replay or external payment processor.

## 1. One writer means all actual paths, not one API gateway

A capability's writer boundary includes **every entry point that can commit, replay, post or issue an irreversible effect**, not just the web channel. The same transaction may reach the ledger through an online transaction manager, night batch, ATM/POS switch, call center, branch backlog, file ingestion, scheduler, repair operator or privileged update. This is a **discovery checklist**: a particular customer may use none, some or other routes. Their presence or absence requires source-owner evidence; do not invent a topology.

| Family in the structural intake | Evidence to discover from the customer | Failure if ignored |
| --- | --- | --- |
| `online_legacy` | CICS, IMS, other online transactions; routing/terminal and real commit ownership | Old online path still posts after route switch |
| `batch_scheduler` | JCL, scheduler, EOD/EOM, reconciliation and delayed updates | Overnight batch reopens old authority |
| `channels` | ATM/POS authorization/posting boundary, mobile/web/back-office connections | Channel retry becomes a second financial effect |
| `branches_offline` | Store-and-forward, branch local queues, disconnection/reconnection epochs | Old offline command arrives after promotion |
| `asynchronous_replay` | MQ, CDC, file transfer, retries, dead letter, dedupe state and sequence | Replayed event double posts or crosses epoch |
| `privileged_operations` | Manual corrections, operator tools, privileged SQL/Db2 updates, recovery utilities | Non-cooperative bypass breaks source fencing |
| `external_effects` | Settlement/payment network, cash dispense, external processor, audit/outbox | Local ledger rollback cannot undo outside effect |

For each family, record `UNKNOWN`, `IN_SCOPE`, or `OUT_OF_SCOPE`. `OUT_OF_SCOPE` is not the default: it needs source-owner exclusion proof. For `IN_SCOPE`, supply evidence for inventory, an **incumbent-enforced** fence, in-flight UNKNOWN, idempotent replay, authoritative SQL/ledger reconciliation and external-effect reconciliation. Where no external effects are possible, explicitly demonstrate that absence through the owner-reviewed scope rather than inventing a successful payment test.

## 2. What must change in the actual client environment

### A. Source transaction admission and revocation

The **legacy transaction processor or a boundary it cannot bypass** must check authority before accepting a new CAP-007 financial command. An API gateway flag is insufficient when batch and internal applications can write independently. Revocation must be durable, ordered and observable. A lease or fencing token must be checked *at the financial writer* and cannot be trusted if an old process retains a live connection that may still COMMIT.

The customer's platform may use transactional admission controls, a service-specific enable/disable mechanism, a database-enforced guard, or controlled quiescing of CICS/IMS/batch entry points. Those alternatives must be designed with platform specialists; they are **not interchangeable**, and a global lock held across a mainframe and PostgreSQL is neither assumed nor promised. Document the concrete commit/visibility boundary and privileges that can bypass it.

### B. Safe handover / logical authority epoch

1. Define a **capability and account/cohort scope** with unambiguous currency, value date, operation ID and owner-approved policy.
2. Inventory online, batch, asynchronous, offline and privileged write paths; stop new admission on *all affected incumbent routes*, with rollback/abort plan.
3. Persist an auditable intent to switch, identify all already admitted operations and every unresolved `UNKNOWN`; prevent the candidate from writing while incumbent ownership is not conclusively fenced.
4. Wait for, terminate safely or independently reconcile every in-flight old transaction and external side effect. A missing reply does **not** establish a rollback. For truly disconnected queues, define version/epoch acceptance and reject or safely transform stale deliveries under approved policy.
5. Stage and independently reconcile balances, operation decisions, postings, outbox, relevant pending events and authoritative watermarks. A copied snapshot is insufficient without a consistent cut/CDC catch-up boundary.
6. Activate the candidate **only once** authority has been revoked from the source and the approved reconciliation gate passes. Record the effective epoch, cutover time interval and independent witness.
7. Do not claim the transition is a distributed atomic COMMIT. Post-switch candidate-origin decisions generally make simple rollback unsafe: switch-back is a **new migration** requiring source catch-up, explicit reconciliation and a new fence.

When independent source fencing is impossible, restrict migration to a smaller capability/cohort or retain the incumbent as the single writer and build read-only projections. **Never** use parallel financial writers as a comparison strategy.

### C. Authorization, Golden Master and Oracle Gates

- The **observed Golden Master** characterizes current legacy behavior; it may be anomalous or obsolete. Keep it distinct from the **owner-approved intended policy**.
- Require a reproducible, authorized, redacted/synthetic trace capture: request/response, internal decisions where available, ledger state, settlement and audit, with capture dates, versions and data minimization.
- Preserve G2 `INCONCLUSIVE` until an accountable owner approves baseline and exceptions. G5 independent oracle must cover negative cases and changed candidate behavior; G6 `BLOCK` until authorized signoff tied to candidate, environment and exact evidence.
- A hash/URI in an intake form is a **claim to review**, not cryptographic signature validation or business approval. The structural checker below can never grant G2/G6 PASS.

## 3. Failure and counterexample matrix for the next genuine campaign

| Case | Fault / action | Required independent evidence and decision |
| --- | --- | --- |
| F01 | Old online writer receives a transfer after switch and stale epoch | Source rejects *before* any financial COMMIT; old DB/VSAM/posting and external effects unchanged |
| F02 | Night batch starts on obsolete schedule after promotion | Its effective source write path is blocked or safely routed; no unjournaled posting |
| F03 | Offline branch retries an old request after reconnect | Stable operation ID/epoch handled by owner-approved policy; no double posting or illegal late commit |
| F04 | Source transaction COMMITs but gateway/controller loses ACK | Decision remains UNKNOWN until independent source + effects reconciliation; no false rollback or second writer |
| F05 | Crash between source fence and candidate activation | Durable intent; safe recovery without dual authority or loss of accepted operations |
| F06 | Candidate COMMITs but response is lost; replay same ID and changed fingerprint | Idempotent original decision, conflict rejection, exactly paired postings and one outbox per accepted operation |
| F07 | Privileged source utility bypasses ordinary gateway | Either prevented by actual authority boundary or a failing control **blocks cutover** |
| F08 | Cash/payment instruction leaves source before cutover; response late or duplicated | Reconcile processor/settlement references and reversal/compensation status; do not infer from internal SQL alone |
| F09 | CDC/file backlog and snapshot watermark disagree | Keep source authoritative and G6 BLOCK until caught up and independently reconciled |
| F10 | Attempt rollback after candidate-origin writes | Reject a simple route toggle; require new staged/fenced/reconciled migration |
| F11 | Operator disables controller, changes connection or replays an old epoch | Fail closed at each incumbent and candidate write entry point; preserve attempt logs |
| F12 | One host/network partition and eventually restored channels | Only assert HA/RPO/RTO supported by independent physical/topological evidence; reconcile unknowns and side effects |

**Evidence per case:** source/target identities and version, exact commands, time bounds/clock uncertainty, original transport logs, source DB/transaction logs or authorized equivalent, independent candidate SQL snapshots, outbox and external settlement acknowledgments, negative controls, SHA-256 and failure history. A bank-provided extract must be stored securely under an approved retention model; **never commit raw customer financial data to this public repository**. Unavailable source evidence yields `INCONCLUSIVE`, not PASS.

## 4. Deliverable now: fail-closed intake evaluator

Code and tests (English only): [`lab/brownfield/owner_readiness/`](../lab/brownfield/owner_readiness/README.md).

```bash
python3 -m unittest discover -s lab/brownfield/owner_readiness -p "test_*.py" -v
python3 lab/brownfield/owner_readiness/assess.py \
  lab/brownfield/owner_readiness/intake.example.json
# Expected NOT_READY with exit 2 — this is the correct default, not a failed bank test.
```

The checker validates the **completeness and shape** of declarations for all source-path families and mandatory proof references. It prevents self-asserted `todmG6=PASS`, duplicate families, fabricated scope omissions without evidence, missing fence references and malformed digests. A maximally filled fake dossier can reach only `READY_FOR_INDEPENDENT_REVIEW`. It **does not download evidence, validate signatures, inspect CICS/IMS/Db2, replay transfers, prove source fencing, approve the Golden Master or authorize production**.

This is a useful `G0/G1` intake control that helps identify *what must be witnessed*, not a G2/G6 approval engine. Historical C2 SQL and controller tests, negative artifacts and SHA are untouched.

## Native source capture platform assessment

The [source-native capture assessment EN](research/source-native-capture-assessment.en.md) / [ES](research/source-native-capture-assessment.es.md) and [structural intake](../lab/brownfield/source_capture/README.md) distinguish Db2 z/OS, VSAM CICS/non-RLS batch, IMS online/DL-I, IBM i journals and unverified vendor systems. **CDC is not source-writer fencing or external-effect reconciliation**; nothing in the new catalog verifies a real installation. The seven candidate families default to UNKNOWN, G2 remains INCONCLUSIVE and G6 BLOCK.

## 5. Acceptance route and scope boundaries

| Stage | Owner | Required output | State today |
| --- | --- | --- | --- |
| Discover source write paths and policy | Customer source/system owners | Verified applicability and operational/decommissioning schedule | **UNKNOWN** |
| Implement real source-enforced fence | Mainframe/legacy team with database and security owners | Source-side negative test, no bypass, late/in-flight reconciliation | **NOT DEMONSTRATED** |
| Reconcile financial and external effects | Finance operations, ledger/payment owners | Independent decision, postings, outbox, settlement/cash evidence | **NOT DEMONSTRATED** |
| Independently review Golden Master and rules | Business owner / oracle reviewers | Approved behavioral contract, rejected defects and exceptions | **NOT APPROVED** |
| Technical/operational decision | Independent reviewers, release authority | Full campaign evidence and TODM G2/G5/G6 decisions | **G2 INCONCLUSIVE / G6 BLOCK** |

This new preparation increment **does not close issue #58**; the owner-controlled and physical external campaign remains legitimately open. No release, bank approval, E2 experimental claim, or mainframe performance equivalence is implied. [Existing C2 directional original report](../evidence/runs/BROWNFIELD-CONTROLLER-PARTITION.md) documents precisely what the current one-runner fixture did verify.
