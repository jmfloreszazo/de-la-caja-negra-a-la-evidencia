# Research: decomposing a mainframe without breaking the business

> **Status:** research and design contract; NOT an executed experiment or a universal recommendation. Tracks issue #32. Published release v2026.10.29 is unchanged.

## The extraction unit is not a COBOL program

Legacy boundaries require evidence from business capabilities, transactional invariants, and actual runtime topology. A CICS program may participate in multiple journeys; multiple applications and JCL jobs may share the same rule or balance. One-to-one translation of programs, COPYBOOKs, or tables carries coupling forward and can duplicate authority.

## Five independent evidence sources

| Source | Contribution | Does not establish |
|---|---|---|
| Event Storming with domain experts | Business events, decisions, exceptions, owners | Runtime topology or permission to split an atomic transaction |
| Strategic DDD | Bounded contexts, ubiquitous language, contracts, accountability | That every context must become a microservice |
| Static archaeology | Static/dynamic CALL, copybooks, SQL, LINK/XCTL, JCL, datasets, MQ | Dependencies visible only at runtime |
| Operational traces | Authorized CICS/IMS, Db2, SMF, batch, queues, peaks, close cycles | Representative coverage across all business periods |
| Independent oracles | Conservation, authorization, idempotency, ordering, reconciliation, recovery | That synthetic tests represent production |

## Falsifiable extraction hypothesis

**Hypothesis:** extract the transaction-history query from posting without duplicating ledger authority. **Falsifier:** the query requires an inseparable synchronous UPDATE/COMMIT view, or measured lag violates the authorization/SLA contract. In either case the proposed split fails the gate.

### Banking example: transfers and statements

1. **Command:** TransferRequested with stable operationId; authentication, authorization, limits, and fraud controls remain explicit obligations.
2. **ACID boundary:** a transfer commits paired postings, operation state, and outbox under ONE transactional authority. An Orleans actor is not a substitute for SQL COMMIT.
3. **Projection:** LedgerEntryCommitted updates a read-only statement model; an idempotent consumer can retry and reorder only as permitted by the published ordering contract.
4. **Reconciliation:** stale read models expose a watermark, fall back to an authorized consistent read, or reject; never present stale projections as authoritative available balance.
5. **Rollback:** if idempotency, balances, latency, or replay fails, restore versioned routing to the legacy path.

## Architecture decision: retain, wrap, extract, retire

| Choice | Preconditions | Exit gate |
|---|---|---|
| Retain on mainframe | Opaque shared ACID or critical operation without an independent oracle | Risk inventory and operation owner |
| Wrap via API/ACL | Stable contract but legacy remains required | Traces, latency, security and reconciliation |
| Extract projection | Eventual consistency explicitly tolerated and measured | Watermark, replay, idempotency, SLA |
| Extract command/domain | Single state authority, proven invariants and rollback | Dual-run, shadow, canary and reversal |
| Retire | No remaining consumer, job or execution path | Representative non-use evidence and signoff |

## Next laboratory acceptance contract (English code and READMEs only)

1. Build a synthetic traceable dependency graph with COBOL programs, CICS transactions, tables, JCL jobs, queues and capabilities. Every edge records source, timestamp and confidence.
2. Merge static edges and sampled traces while preserving conflicts and unknown dependencies.
3. Propose bounded context candidates through versioned, inspectable rules, not automatic service-per-program splitting.
4. Emit command/event contracts, state ownership, invariants, batch windows, latency and reversal policies.
5. Add a negative gate rejecting any partition that splits an atomic operation without an approved consistency strategy.
6. Compare retain, modular monolith, strangler, hybrid coexistence and microservices in an ADR with evidence and cost assumptions.
7. Link choices to E1/E2 evidence where available, keeping prototype, actual CI and production distinct.

**Not yet demonstrated:** executable fixture, adversarial controls, independent graph validation, domain-owner review, production workload, and dated TCO. This document contains no accepted experimental result.
