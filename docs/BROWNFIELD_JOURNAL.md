# Brownfield C2 — admission journal, UNKNOWN and crash reconciliation

**Research contract, 1 November 2026. Not customer acceptance.**

The next risk after the two-store coexistence rehearsal is the ambiguous
outcome of a command whose durable PostgreSQL COMMIT precedes an absent ACK.
A missing response is neither a rolled-back transfer nor a safe reason to
route the same operation ID to another financial writer.

The new `bf_control` PostgreSQL database persists the CAP-007 operation ID,
canonical request hash, writer and epoch, synthetic tenant/actor/mandate
references and states `ADMITTED`, `DISPATCHING`, `UNKNOWN`,
`COMMITTED`, `REJECTED` and `RECONCILIATION_REQUIRED`. The gateway
serializes one operation ID among cooperating callers. It can die on either
side of remote COMMIT. A *separate* SQL read-only oracle then examines both
stores and finalizes only a matching durable decision. If no decision can be
observed, it keeps UNKNOWN; it never invents REJECTED.

## Mandatory negative controls

- A crash after admission but before send cannot be promoted to a rejection.
- A crash after remote COMMIT but before gateway journal update must be
  recoverable as one committed financial effect.
- A changed operation fingerprint must fail, even after a successful ACK.
- A forged terminal journal decision must fail an independent SQL audit.
- Cutover is blocked by unresolved or unjournaled operations, while rollback
  after candidate-origin decisions is vetoed.
- Controller/candidate epoch disagreement must deny new gateway admissions.

## Integrated status and remaining assurance

PR #69 adds persisted SQL enrollment in both adapters. After enrollment,
removing the environment flag cannot permit unadmitted writes; the standalone
authority-switch CLI must also refuse a bypass. Before changing epochs, the
coordinator commits a PREPARED intent and SWITCHING traffic freeze. External
SIGKILL controls exercise forward recovery between authority COMMITs. This
is not distributed atomic COMMIT.

[Main CI #41353221630](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41353221630)
passed 20 controls on `279ca566`; both SQL oracles 10/10. The
[earlier 19-control evidence](../evidence/runs/BROWNFIELD-C2-RECOVERY.md)
remains an observation of its own SHA, including the first failure.

In-flight controller partitions, lock loss, remaining process/reply windows
and external-side-effect reconciliation are still open. Privileged raw SQL
and a noncooperating mainframe remain outside application fencing. Three
containers share one runner; no physical HA, RTO/RPO or actual bank authority
is established. G2=INCONCLUSIVE, G6=BLOCK; #64/#58 open, #53 frozen. No release
has changed.
