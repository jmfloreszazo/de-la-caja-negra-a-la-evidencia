# Companion chapter · Decomposing a mainframe with evidence

> **Editorial review draft.** Not part of published v2026.10.29. Tracks issue #32.

## The boundary is not the program

Modernizing a banking core does not begin by distributing COBOL paragraphs across containers. Reconstruct the business responsibility, data authority, temporal dependencies and actual transactional contract first. A `CALL` is a technical dependency, not necessarily a bounded context. A shared table may support historical queries, accounting postings or authorization controls.

## Discover before dividing

**Event Storming** reconstructs what happened, who made decisions and which exceptions matter, from ATM cash withdrawal to end-of-day reversals. Event Storming is not **Event Sourcing**: discovery does not require an append-only event store.

**Strategic DDD** suggests bounded contexts and ownership. Validate those hypotheses against static COBOL/CICS LINK/XCTL/copybook/SQL/JCL/Db2/VSAM/MQ evidence, authorized runtime traces and operational constraints such as closing, reconciliation and peak periods. Absence from a sampled trace is never proof of nonexistence.

## A banking transfer example

Consider a stable operation identifier whose transfer atomically commits two balanced postings, an operation record and an outbox message. Moving one posting to a new service while leaving the other on the mainframe can alter business semantics. An actor or saga does not automatically replace the original ACID boundary.

A statement projection, however, may be a first extraction candidate if it provides explicit idempotency, watermark, rebuild, lag tolerance, authorization and a consistent-read fallback. An eventually consistent statement must never masquerade as the authoritative balance for dispensing cash.

## An oracle that can refuse

The synthetic `lab/decomposition/` design oracle preserves the source of every dependency: static, runtime or domain-expert. Disagreement about atomicity is not resolved by choosing the more convenient answer: it rejects the cut. Atomic transaction members form one indivisible group even if they are not directly linked by a single graph edge. Cuts crossing unknown or inferred dependencies are also rejected.

`CANDIDATE_ONLY` **does not authorize a migration**. It means the proposal does not contradict currently encoded constraints in a small synthetic graph. A real decision requires representative observations, business owners, negative and recovery tests, workload performance, dated cost evidence and rollback proof.

## Five possible decisions

Retain the legacy core if critical invariants cannot yet be reproduced. Wrap it with an API and Anti-Corruption Layer to move the boundary without moving state authority. Extract queries to evaluate consistency explicitly. Extract commands only after proving ownership, atomicity or an approved new compensation contract. Retire an asset only after demonstrating no remaining seasonal job, remote terminal, consumer or recovery dependency.

**The governing rule:** prove the responsibility boundary before picking deployment topology. When new evidence falsifies the proposed boundary, revise the design, not the evidence.

## Evidence contract

This is methodological reasoning backed by a **synthetic graph**, not live bank traces, IBM Z measurements or production acceptance. Laboratory checks evaluate structural decisions only. See [research protocol](../../../docs/research/mainframe-decomposition.en.md) and [laboratory](../../../lab/decomposition/README.md).
