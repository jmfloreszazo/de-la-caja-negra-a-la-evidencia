**English** · [Español](../../es/anexos/anexo-d-decisiones-de-arquitectura.md)

[← Annex C · Reference run](annex-c-reference-run.md) · [Contents](../README.md) · [Annex E · Catalog of one hundred risks →](annex-e-catalog-of-one-hundred-risks.md)

# Annex D · Architecture decisions

## Decisions for a modernization

**ADR-001: The golden master is not the only truth.** It will be checked against approved rules and invariants; an intentional difference will have an explicit business decision.

**ADR-002: An account is not necessarily an ACID boundary.** The actor coordinates an identity; the ledger defines the source of truth and the commit of related operations.

**ADR-003: Avoid uncoordinated dual writes.** Coexistence relies on a single writer, an outbox, controlled CDC and reconciliation.

**ADR-004: Do not move functionality by program equivalence.** Seams are designed around business capabilities and data ownership.

**ADR-005: The benchmark includes failures.** There is no capacity acceptance without rehearsed durability, consistency, skewed load and recovery.

**ADR-006: AI does not approve its own tests.** The baseline and the trusted verifiers have owners and permissions different from those of the builder agent.

**ADR-007: A 1:1 translator can be temporary.** A documented exception is kept, with scope, review date and exit criteria.

## Lab decisions

**Keep two references.** The COBOL execution provides observed behaviour; the approvable cases provide the normative expectation. A discrepancy between them must be resolved, not hidden.

**Separate processes.** Candidate and gate run as different programs. This makes the separation understandable and prepares a future permissions boundary. In the local package there is no security isolation between their authors.

**Use a small policy.** The fee and the threshold allow checking concrete errors. The case does not try to represent a banking core.

**Keep reproduction free of a remote model.** Deterministic execution makes results easy to repeat. Autonomous construction with agents requires a separate experiment.

**Record the environment.** The summary keeps tool versions and source hashes. A new run must generate its own record.

**Do not publish to production.** SIMULATED_ALLOW is a lab label. It deploys nothing, grants no privileges and does not represent a human signature.

---

[← Annex C · Reference run](annex-c-reference-run.md) · [Contents](../README.md) · [Annex E · Catalog of one hundred risks →](annex-e-catalog-of-one-hundred-risks.md)
