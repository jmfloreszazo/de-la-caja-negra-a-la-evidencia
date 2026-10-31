# Recover business functionality to build a new system from scratch

> **EN research draft — issue #32.** This explicitly replaces the idea of parsing COBOL into microservices with **discovering capabilities and implementing a new system from first principles**. The accompanying banking catalog contains reference hypotheses, not requirements observed in a real institution or signed off by an owner.

## What we need to know

The question is not which COBOL paragraphs to port. It is **which business capabilities exist, what outcomes they promise, what exceptions they handle, and which guarantees must survive**. We may replace the implementation completely while preserving authorized business contracts. Long-hidden exceptions and operational calendars are part of the contract.

The incumbent system is one source of **observations**, never the sole oracle of correctness. A legacy defect does not automatically become a required feature. Approved business policy and independent verification must resolve discrepancies.

## Thirty hypothetical capabilities across twelve domains

The [English-only machine-readable catalog](../../lab/decomposition/functional_capabilities.json) covers customer identity, accounts, payments, cards/ATM, interest/pricing, lending, general ledger, batch operations, risk/compliance, resilience, channels, and external integration. Each record includes objective, trigger, outcome, exceptional paths, invariant, consistency needs, criticality, Given/When/Then scenarios, unanswered questions, accountable owner and evidence references.

**All thirty start as `HYPOTHESIS_NOT_OBSERVED`.** This is not an enterprise inventory or an assertion that every bank supports every item.

## Discovery without source-code parsing

1. **Capability map with accountable business owners:** interview operations, accounting, fraud, channels, product, customer service, audit and controls. Distinguish policies from tribal knowledge and exceptions.
2. **Journeys and business events:** Event Storming reconstructs commands, decisions, outcomes, manual overrides and calendars for transfers, ATM withdrawals, reversals and end-of-day.
3. **Observable business contracts:** existing APIs, files, externally visible states, receipts, ATM switch and clearing agreements; distinguish instruction receipt, posting and external settlement.
4. **Authorized black-box characterization:** representative anonymized or synthetic inputs and outputs, timestamps, postings, reconciliation and failure outcomes keyed by stable business identifiers. Never upload sensitive banking data into a public repository.
5. **Independent oracles:** approved money, mandate, limits, idempotency, closing and recovery rules. Validate both incumbent and new implementation against these rules, not only against each other.
6. **Negative counterexamples:** replay after a lost COMMIT acknowledgement, network partitions, failed cash dispensing, repeated requests, partial EOD, late events and cross-border calendar edge cases.
7. **Design from scratch:** choose modules, state authority and deployment based on validated contracts. A modular monolith is often a defensible first implementation; microservices are not automatic.

## Worked capability contract: internal transfer (CAP-007)

**Business expectation:** a valid authorized transfer with a stable operation ID, sufficient funds and approved limits durably records balanced postings, operation status and outbox under one transaction authority. Losing the client ACK can make the result `UNKNOWN`, not necessarily rolled back.

| Scenario | Required result | Independent check |
|---|---|---|
| Valid transfer | Durable balanced entries and operation | Conserved total, paired postings and outbox |
| Reused operation ID | No second financial effect | ID cardinality and final authoritative state |
| Insufficient balance | Rejection without debit | Before/after ledger and audit |
| Crash after COMMIT before ACK | Uncertain reply and safe query/replay | SQL authority and exact operation effects |

A possible greenfield implementation is a .NET 10 domain service with PostgreSQL as accounting authority, durable idempotency and transactional outbox. Orleans is optional coordination rather than a substitute for ACID. REST at channel boundaries and internal gRPC must be justified by the deployment contract and measurements. This is an architectural hypothesis, not a mandated design.

## ATM: authorization is not dispensing (CAP-011/012)

Authorization, reserving funds and physically dispensing cash are different events. A failure to dispense can require network-specific reversal and reconciliation. An authorization ACK is not proof that a customer received cash. Capture response codes, timeouts, partial dispense, switch advice, fraud limits and reconciliation authority.

## End-of-day is more than a scheduled job (CAP-020/021/022)

Closing has business dates, time zones, control totals, ordered dependencies, checkpoints, restarts, late messages and audit obligations. Replacing a JCL job with cron does not prove the same contract. Define period ownership, completion gates, re-open/correction policy and prevention of double postings.

## An implementation-ready capability specification

Require owner and approved policy; commands/queries/events; state ownership; positive and negative examples; transactional/consistency scope; timeout/retry/compensation behavior; security and audit obligations; quantitative load, p99, availability, RTO/RPO, calendar and cost requirements; external dependencies; executable acceptance conditions and **independent** oracle; reproducible provenance and ADR.

The output becomes `intent.md`, `spec.md`, English Gherkin acceptance scenarios, API/event contracts, ADRs and Oracle Gates. Resolve mismatch between legacy behavior and policy as either **preserve, fix, or deliberate change** with human signoff rather than copying accidental implementation behavior.

## Evidence boundary and next experiment

[functional_contract_gate.py](../../lab/decomposition/functional_contract_gate.py) checks structure and evidence-readiness but never grants real business approval. The initial thirty records must all report `NEEDS_EVIDENCE`. No bank traces, real mainframe behavior, institution-specific regulation or IBM Z performance equivalent is asserted.

The next useful vertical slice is internal transfer plus statement projection: secure an approved policy and cases, build an independent oracle, then implement the new capability and test durable retry, failure and reconciliation before expanding the scope.
