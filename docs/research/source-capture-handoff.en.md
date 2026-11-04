# Proving the synthetic snapshot-to-journal handoff

**#58 · 4 November 2026 · EN research.** [Español](source-capture-handoff.es.md) · [existing source-native discovery](source-native-capture-assessment.en.md) · [synthetic W01 journal evidence](../../evidence/runs/W01-SOURCE-JOURNAL.md).

## Why the original platform interview was insufficient

A vendor product manual and a complete list of writer paths are **necessary, not sufficient**. A system can have logs and still skip an update between the initial snapshot and the first streaming cursor, replay an already-committed operation, consume a stream from the wrong incarnation, or acknowledge a partial target state. The previous 22/22 platform-assessment checks only tested **declarations and metadata**, not a change stream.

The new [English-only source-neutral test oracle](../../lab/brownfield/source_capture/handoff.py) uses an independent **synthetic** source commit trace and compares three things: (1) balances exactly at the snapshot cut, (2) the committed ordered tail after that cut, and (3) final balances and cursor after target replay. This deliberately **does not parse** COBOL, JCL, data definition files, physical Db2/IMS logs, VSAM record layouts or proprietary CDC formats.

## Test model

- Four synthetic accounts, each opening at 100,000 minor units. Exactly five independently declared committed transfers, with the initial cut after sequence 2 and events 3–5 consumed later.
- Each transaction has a unique operation ID, ordered source sequence and paired debit/credit amount. An explicitly aborted operation must **not** be treated as committed.
- The snapshot carries a source epoch and the cut at sequence 2; the captured consumer starts **after the same cursor**; the declared oldest retained sequence must permit replay from that cut.
- The capture must match the source fixture's committed tail exactly: no missing, extra, duplicate, reordered, tampered or aborted event. The target must have the correct applied cursor and all independently replayed balances.
- Mismatched source epochs, expired log retention, a partial snapshot, stale target, unauthorized self-asserted acceptance or malformed traces fail closed.
- Twenty-six unit tests include deliberately bad input and CLI return-code checks. This is an **offline Python-only oracle**, not a live physical failure/restart test.

The test source fixture itself is **not** independent of an actual customer's DBMS. A fully fabricated but internally consistent source history and captured tail could pass this oracle. Production methodology therefore requires customer-owned original snapshots and log evidence, independently authenticated source commits/transaction outcomes, durable source identity and retention proofs, all online/batch/utility/offline paths, external-effects reconciliation and owner-approved policy. The tool never fetches customer evidence, checks signatures or establishes source authority.

## Interpreting outputs

| Output | Meaning |
| --- | --- |
| `PASS_SYNTHETIC_HANDOFF_ORACLE` | Internal consistency proven **for synthetic fixture** only |
| `REJECT` | A meaningful cut, ordering, replay or target inconsistency was found |
| `INVALID` | Unrecognized source, malformed schema or forbidden approval flags |

All statuses, including a passing synthetic trace, retain **TODM G2=INCONCLUSIVE; G6=BLOCK**, `productionApproved=false`, `nativeCaptureTestExecuted=false`, and `externalEffectsReconciled=false`. The platform catalog's seven families are used **only as labels**, never as proof that a native source was tested. W01's original 22/22 PostgreSQL experiment is separate and not repurposed as a Db2/VSAM result.

## Roadmap and evidence needed

The next real #58 acceptance contract is a **bank/owner-produced, versioned test trace**, with a source-signed or independently attested snapshot bookmark and contiguous committed UOR log, explicit restart/retention limits, comparison with a second independent source oracle and negative injection covering the actual vendor log reader. The current work is a falsifiable protocol and fixture to help identify missing evidence, **not** production cutover authorization. #53 remains frozen, E2 `partially_verified`, no new release.

[Runbook (English)](../../lab/brownfield/source_capture/README.md). The [original exact-head CI #41908404394](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41908404394) has now executed **26/26 synthetic controls PASS**, with the original artifact ZIP downloaded and independently SHA-256 checked. See the [EN audit](../../evidence/runs/SOURCE-HANDOFF.md) / [ES audit](../../evidence/runs/SOURCE-HANDOFF.es.md). This is **not** a native-source CDC or banking PASS.
