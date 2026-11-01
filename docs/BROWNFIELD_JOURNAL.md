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

## Critical missing assurance

The existing legacy Python CLI and .NET candidate CLI can be called without
the gateway, so **their SQL writes are not yet fenced by the third controller**.
The existing candidate-store `FOR SHARE` epoch fence remains cooperative.
The controller and candidate authority epochs are changed in separate
transactions: there is no distributed atomic update or split-authority
crash-repair proof. A direct rogue writer can bypass admission, and external
payment processors are unmodeled. This is a bounded engineering step, not
2PC, a production switch or a real IBM Z fence.

The three disposable databases run in containers **on one runner**, not three
physical failure domains. The journal contains synthetic fixture identity
strings, not bank authorization. TODM G2 remains INCONCLUSIVE and G6 BLOCK.

**Evidence status:** SOURCE CANDIDATE until the original CI at an exact head
SHA passes and retains raw logs/artifact digests. See issue #64; #58 remains
open. No change to published book release or to frozen #53.

### C2 adapter enforcement experiment

With `BROWNFIELD_REQUIRE_CONTROLLER=YES`, both the Python legacy adapter and
.NET candidate require reachable `bf_control` and retain a shared authority
row lock until the financial database transaction completes. The original
legacy two-store experiment is unaffected when this opt-in flag is absent.
In strict mode, both adapters additionally require a matching persisted
`DISPATCHING` journal row; direct unadmitted commands are rejected. If the
opt-in requirement is deliberately disabled, unjournaled posting is still
possible; the independent oracle detects, but cannot prevent, this
configuration bypass. This is not a genuine IBM Z fence.
