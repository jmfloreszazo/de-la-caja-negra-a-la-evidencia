**English** · [Español](../../es/anexos/anexo-f-glosario-operativo.md)

[← Annex E · Catalog of one hundred risks](annex-e-catalog-of-one-hundred-risks.md) · [Contents](../README.md) · [Annex G · Sources and scope of the research →](annex-g-sources-and-scope-of-the-research.md)

# Annex F · Operational glossary

| Term | Meaning in this book |
|---|---|
| ACID | Atomicity, consistency, isolation and durability, within the boundary supported by the specific transactional system |
| ACL | Anti-corruption layer: translates legacy formats and semantics so they do not contaminate the new model |
| Actor | Logical entity with identity that processes messages in turns; in Orleans, a grain |
| ADR | Architecture decision record, with context, alternatives and consequences |
| Baseline | Approved, versioned set of expected behaviours against which a candidate is judged |
| Batch | Batch work, often with dependencies, windows, checkpoints and restarts |
| CDC | Change data capture from a source system |
| CICS | Transaction processing platform in IBM environments |
| COMP-3 | Packed decimal representation: two digits per byte and the sign in the last nibble |
| Copybook | Reusable COBOL fragment, usually a shared data definition |
| Coordinated omission | Measurement error in which the generator stops offering load while the system is stalled |
| Deadlock | A cycle of waits between transactions that prevents progress; the engine chooses a victim |
| Fencing | Technique that lets the store reject writes from an owner whose epoch is no longer current |
| Golden master | Reference observation of existing behaviour, useful but not infallible |
| Idempotency | Repeating an identifiable command without repeating its business effect |
| INCONCLUSIVE | Verdict indicating the evidence does not allow a conclusion; it blocks delivery by default |
| JCL | Job control language that organizes batch execution on z/OS |
| Ledger | Authoritative accounting record, with traceability of movements |
| Mandate | Authorization bounded in scope, time, budget and actions for an agent or a person |
| MIPS / MSU | Capacity and consumption metrics from mainframe contexts; they are not equivalent to vCPUs |
| Oracle | Mechanism that answers whether a result is correct: approved examples, properties, decision tables or comparison |
| Oracle Gate | Automatable decision that checks an obligation against independent evidence |
| Outbox | Pending event written in the same transaction as the state change |
| REA | Reverse Engineer Anything: MCP server and CLI that connects agents to analysis tools and an evidence contract |
| REDEFINES | COBOL clause that describes the same memory region with another structure |
| RPO / RTO | Agreed maximum data loss and recovery time |
| Saga | Coordination of a distributed process through steps and compensations, when the business allows it |
| Strangler Fig | Incremental replacement of legacy capabilities behind a facade |
| Syncpoint | Point at which CICS commits or backs out the unit of work over recoverable resources |
| TODM | Test Oracle-Driven Methodology: governed acceptance through independent oracles and gates G0–G7 |
| VSAM | Family of file access methods on IBM systems |
| WLM | Workload and priority management on z/OS |

---

[← Annex E · Catalog of one hundred risks](annex-e-catalog-of-one-hundred-risks.md) · [Contents](../README.md) · [Annex G · Sources and scope of the research →](annex-g-sources-and-scope-of-the-research.md)
