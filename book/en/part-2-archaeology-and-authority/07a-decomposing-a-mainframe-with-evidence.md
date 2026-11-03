**English** · [Español](../../es/parte-2-arqueologia-y-autoridad/07a-descomponer-el-mainframe-con-evidencia.md)

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

## Source-platform interview and assessment

Archaeology starts with a structured interview and continues by checking each answer against evidence. The platform may be IBM Z with z/OS, IBM i on Power, Fujitsu BS2000 or another environment; the COBOL language alone identifies neither the operating system nor the data manager. Record the actual vendor, model, release, partition and installed products before drawing conclusions. Include IBM i as an adjacent enterprise platform and keep the BS2000 interview separate from the GS21/MSP/XSP discovery entry; vendor identity alone does not establish shared behavior.

The interview brings together business, development, operations, data, security and infrastructure specialists. It identifies capabilities and owners; languages and source; data managers and files; transactions and locks; jobs and batch windows; interfaces, file transfers, branches, continuity, metrics and costs. Record the owner, date, source, scope and limitations of each answer. An expert statement is a hypothesis until checked against source, configuration, observations and representative tests; absence from a sampled trace does not establish that a dependency is absent.

| Environment or technology | Initial question |
|---|---|
| IBM Z and z/OS | Are CICS, IMS DB or TM, Db2 for z/OS, VSAM and JCL used? |
| IBM i | Which RPG, COBOL and CL programs access Db2 for i and physical and logical files [60]? |
| Fujitsu BS2000 | Which releases of COBOL2000, openUTM, UDS/SQL, SESAM/SQL or openFT are installed [61]? |
| Other products | Are Natural, Adabas, IDMS, Datacom or a Unisys platform present, and which releases and interfaces are used? |

Verify each product's presence: these are examples, not mandatory components of an architecture. IMS DB and IMS TM serve different functions. VSAM organizes and provides access to data sets; investigate keys, ordering and encoding before selecting a target structure.

### From interview to a verifiable decision

For each capability, identify rules, data, write authority, transaction boundaries, consumers and acceptance criteria. Record unknowns and decide what can be retained, wrapped, progressively replaced or retired, with a rationale and test for each decision. A saga or an actor does not automatically replace an atomic transaction.

Compare on-premises, cloud and hybrid alternatives using equivalent workloads and periods, volumes, latency, batch windows, recovery, security, dated costs and constraints. MIPS, MSU and CPW are not interchangeable units and do not convert directly to core counts. IBM describes CPW as a relative commercial-workload capacity measure whose result depends on workload characteristics [62]. Differential tests use controlled inputs, edge cases and reference outputs; investigate and approve differences. Do not treat a synthetic experiment or shared runner as a mainframe measurement or production test.

For the platform-layer evidence questionnaire, use [Chapter 1](../part-1-before-translating/01-the-mainframe-is-not-a-fast-box.md). For source-scoped pattern decisions, use [Chapter 13](../part-4-patterns/13-before-choosing-a-pattern-identify-the-contract.md) and the [catalog scope](../../../research/platform-contracts/README.md). The interview records discovery hypotheses; it does not promote the catalog's unverified families or adjacent platforms to verified migrations.

## Evidence contract

This is methodological reasoning backed by a **synthetic graph**, not live bank traces, IBM Z measurements or production acceptance. Laboratory checks evaluate structural decisions only. See [research protocol](../../../docs/research/mainframe-decomposition.en.md) and [laboratory](../../../lab/decomposition/README.md).
