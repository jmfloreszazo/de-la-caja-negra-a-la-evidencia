**English** · [Español](../../es/parte-4-patrones/13-antes-de-elegir-un-patron-identifica-el-contrato.md)

[← Part IV · Patterns that replace responsibilities, not syntax](README.md) · [Contents](../README.md) · [Chapter 14 · Strangler Fig: change the edge before the heart →](14-strangler-fig-change-the-edge-before-the-heart.md)

# Chapter 13 · Before choosing a pattern, identify the contract

> [!IMPORTANT]
> **Chapter thesis.** A pattern is chosen by invariant, load and failure boundary, not by fashion. First the property we want to preserve; then the minimum mechanism that satisfies it outside its original platform.

In architecture we tend to use patterns as if they were pieces from a catalog: actors, sagas, event sourcing, CQRS, microservices. The result can end up as a collection of modern technologies without justification. I would turn the question around. Which property of the old system do I need to preserve? Which new problem appears when I leave its platform? What is the minimum mechanism that satisfies both conditions?

If a COBOL routine accesses a dataset exclusively during a batch window, its behaviour does not necessarily require actors or Kafka. Perhaps it needs a deterministic partition, a single writer and a transactional checkpoint. If an online operation needs to update two tables atomically, a relational database and an ACID transaction may be better than a saga. If the system must query millions of balances, it may need a read projection, not to split every entity into microservices prematurely. A pattern is chosen by invariant, load and failure boundary, not by fashion.

## Substitution matrix

| Legacy responsibility | Candidate pattern | When yes | When it is not enough |
| --- | --- | --- | --- |
| Monolithic program with mixed rules | Strangler Fig + vertical slice | Incremental separation by capability | If there is no safe interception point |
| EBCDIC formats / copybooks | Anti-Corruption Layer + canonical model | Temporary interoperability with a versioned contract | If it hides loss of precision or rounding |
| Data shared by many programs | Data ownership per domain | When a responsible writer can be defined | If hidden writers persist |
| Local ACID update | Transaction Script + Unit of Work | Operation within a single transactional boundary | If it spans resources without a common transaction |
| Operations per account or policy | Actor per identity | Localized contention and encapsulable state | Transfer between actors or a hot account |
| Events to other systems | Outbox + Inbox + idempotency | Reliable publication after commit | It does not turn independent systems into a global ACID |
| Long, compensable flow | Saga / Process Manager | Compensations and acceptable intermediate states | A ledger that requires immediate atomicity |
| Bulk reporting reads | CQRS / read model | Query loads different from write loads | It does not replace the authoritative accounting record |
| Batch of millions of records | Partitioned Batch + checkpoint | Divisible work with stable keys | Global dependencies and strict order |
| Conversational sessions | State Machine + persistent workflow | Explicit states and controlled expiry | Implicit context not yet recovered |
| Transaction retries | Idempotency Key + deduplication | Retries from networks, queues and clients | It does not fix non-idempotent external effects |
| Failure semantics | Bulkhead + timeout + circuit breaker | Isolating degradations | It does not replace reconciliation or rollback |

The matrix is deliberately conditional. There is no pattern that replaces "the mainframe" as a whole. Different guarantees must be rebuilt in different layers.

To read the matrix it helps to ask the same three questions every time, in this order. What did the old system guarantee, even if nobody wrote it down? What new problem appears when we take it off its platform: networks, several instances, another engine, another encoding? What is the simplest mechanism that solves both and that we can test? If a proposal cannot answer the third, it is still a preference, not a design.

> **There is no pattern that replaces "the mainframe" as a whole. Different guarantees must be rebuilt in different layers.**

---

[← Part IV · Patterns that replace responsibilities, not syntax](README.md) · [Contents](../README.md) · [Chapter 14 · Strangler Fig: change the edge before the heart →](14-strangler-fig-change-the-edge-before-the-heart.md)
