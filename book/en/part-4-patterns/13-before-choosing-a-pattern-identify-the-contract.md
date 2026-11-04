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

## Three platform mappings, with different failure contracts

The [machine-readable seed catalog](../../../research/platform-contracts/catalog.json) and its [scope guide](../../../research/platform-contracts/README.md) make the preceding matrix specific. It covers IBM Z/z/OS, Unisys MCP and OS 2200 integration; these are three platform contexts, not interchangeable implementations. The following are proposed replacements and acceptance tests. None was executed against an original vendor runtime for this research increment.

**IBM / CICS and Db2.** Inventory the recoverable resources and actual unit-of-work boundaries before extracting an API [49], [56]. A target SQL transaction is a candidate for resources inside its boundary. If the source also coordinates a queue or another manager, an outbox may require an approved change to externally observable intermediate states. Inject a failure between participants and inspect both resource histories; final balances alone cannot prove the old coordination contract survived.

**Unisys MCP / Enterprise Database Server.** MCP 21 documentation conditions SINGLEABORT on `INDEPENDENTTRANS` and assigns rectification of an aborted transaction to the application/end user [58]. Therefore obtain DASDL/audit settings before designing retries. A candidate must retry the appropriate complete instruction and reconcile its outcome; retrying just the failed statement can omit earlier effects.

**OS 2200 TIP / ePortal.** The ePortal 10 connector can resend after reconnecting; its guidance treats stateful sessions differently [59]. Recover session context and financial identity separately. A new connection is neither proof that the previous instruction failed nor permission to repeat its effect. This source documents a connector, not the complete OS 2200 database recovery model.

| Mapping | Candidate layers | Counterexample and required oracle |
|---|---|---|
| MF006: CICS resource boundary | Application UOW; data transaction; recoverable integration | Separate commits after extraction: crash between effects and reconcile each participant |
| MF009: MCP recovery configuration | Application retry; engine recovery; operational procedure | Statement-only retry loses earlier work: compare the complete expected instruction and unaffected work |
| MF010: TIP reconnect/session | Semantic adapter; session recovery; durable identity | Replay on another session duplicates or misroutes work: compare accepted effect, identity and context |

The schema requires a dated source/version, original contract, candidate layers, semantic gap, failure control, oracle, customer measurements and risk IDs. Its validator rejects invented equivalence, undocumented sources and unsupported evidence states. Six catalog mutations exercise those checks. **These are metadata checks, not six vendor-behavior tests.** Existing SQL/ATM oracles can inform candidate test design; their success does not verify an MCP, OS 2200 or IBM installation.

## A decision sequence for synchronous, asynchronous and batch work

Start with the business deadline and durable owner. If the caller must know the final decision now, keep the minimum authoritative command synchronous and provide status recovery for a lost response. If eventual completion is allowed, acknowledge durable acceptance with a distinct state and correlate the later final result. A queue changes delivery and buffering; it does not grant permission to approve work offline.

Then identify atomicity. Keep immediately inseparable effects in a compatible transaction boundary. Use a saga only when each intermediate state and compensation is permitted. A workflow supplies durable progress across steps; a batch DAG additionally needs immutable input identity, dependencies, restart checkpoints and controlled publication. Neither a scheduler nor one worker per record establishes a correct end-of-day close.

Finally choose placement from measured demand and failure domains. A read projection may offload queries if freshness is explicit. CDC may feed that projection but does not transfer write authority. Horizontal application workers still share database/log/hot-key limits. Retain or integrate the original engine when its contract is unknown, a necessary recovery mechanism has no demonstrated replacement, or a narrower modernization already delivers the business value.

Fujitsu GS21, NEC ACOS, Hitachi VOS and Bull GCOS remain discovery entries without verified feature mappings in this increment. NonStop, OpenVMS, IBM i and HP 3000 are separately marked adjacent research scope. Unknown means that research is still required; it does not mean absent, unsupported or equivalent. The complete #28 inventory and its batch/offline/CDC/cross-border worked examples remain future deliverables. This first seed gives those entries a checkable format instead of presenting a long unreviewed list as completed research.

## The pattern depends on the vendor, subsystem and COMMIT owner

| Documented platform responsibility | Candidate replacement | What the candidate does **not** provide automatically | Essential negative oracle |
| --- | --- | --- | --- |
| IBM Z: CSS/FICON offloads central-CPU I/O | Bounded async queues, durable storage and redundant paths | `async` does not recreate a channel subsystem or its failure domains | Saturate/fail a log storage path and measure durable-commit latency |
| z/OS: WLM service classes | Quotas, admission, priority and horizontal autoscale | CPU limits/HPA do not guarantee the same service goals | Competing loads with per-class p99 |
| Db2 for z/OS: isolation and locks | SQL transaction with explicit retry policy | Similar isolation names do not prove identical concurrent histories | Two transfers, rollback, timeouts and conserved balance |
| IBM i: commitment control and journals | Source-authoritative incremental projection | A journal does not prove the whole channel's transaction boundary | Abort a job and verify no partial posting |
| MCP: Enterprise Database Server Accesses | Key/ordering ACL and domain model | SQL indexes do not establish the same ordering/selection behavior | Ordered record selection, restart and duplicates |
| OS 2200: optional TIP connector resend | Operation-key idempotency and durable outcome lookup | A retry after lost reply can duplicate an effect | COMMIT with lost ACK, retry and exactly one posting |
| Fujitsu GS21 historical product announcement | **Retain / investigate** until installation is identified | An old model name does not establish OS, database, CDC or current support | Reject premature pattern selection without source manuals |

There is no universal *vendor → microservice* mapping. Each candidate must state its infrastructure, application, data, security, operations, exception and failure contracts. **Retain** can be a valid modernization decision when a necessary invariant cannot yet be demonstrated. These are version-scoped documented examples or an explicitly historical announcement; none is an executed vendor-source experiment.

### Two costly anti-patterns

**First:** choose Orleans actors to replace every financial lock. An actor can serialize work per identity; two actors, two storage systems and a payment switch do not thereby share one atomic COMMIT. A single durable writer and SQL transaction, with outbox, audit and idempotency, may preserve a transfer more directly. Actors are optional and must justify what actual contention they solve without inventing financial atomicity.

**Second:** claim production CDC because a synthetic journal is green. The W01 PostgreSQL lab passed 22/22 bounded snapshot/sequence/replay controls, and a separate synthetic handoff oracle passed 26/26. Neither read native Db2/VSAM/IMS logs or proved all online, batch and privileged writers were captured. Real options include proved CDC, a controlled export boundary, a nondouble-writer adapter or **retention** until source guarantees exist.

For each candidate the [machine-readable catalog](../../../research/vendor-runtime-contracts/catalog.json) requires the original contract, pattern, gap, negative test, independent oracle and customer measurements; its metadata controls refuse inflated equivalence or approval. The [EN dossier](../../../docs/research/vendor-runtime-contracts.en.md) and [Spanish edition](../../../docs/research/vendor-runtime-contracts.es.md) hold the operator/DBA/security/business interview.

---

[← Part IV · Patterns that replace responsibilities, not syntax](README.md) · [Contents](../README.md) · [Chapter 14 · Strangler Fig: change the edge before the heart →](14-strangler-fig-change-the-edge-before-the-heart.md)
