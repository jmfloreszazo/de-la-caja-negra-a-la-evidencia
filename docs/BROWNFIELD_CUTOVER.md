# Brownfield CAP-007 / CAP-005 — coexistence, cutover and rollback

**Classification:** design and synthetic rehearsal, **not** a PostgreSQL-backed acceptance experiment. [Español](BROWNFIELD_CUTOVER.es.md) · [Tracking #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58)

## The architectural boundary is financial authority

A replacement written from scratch in .NET 10 is not a greenfield banking project. The existing core already owns customer-visible transactions, business calendars, history, interfaces and audit. The migration boundary is **a business capability and its authoritative data**, never one translated COBOL program per microservice.

A channel adapter / anti-corruption layer may invoke the old implementation or the new one, but a transfer must have **exactly one authoritative writer**. Running both implementations in full write mode as a comparison would create two financial effects. Shadow mode may compare sanitized requests, decisions and read-only representations; its candidate must not publish external payments, ledger postings or outbox events.

## Rehearsal contract (Python only, no production gate)

The source is [`lab/brownfield/coexistence_gate.py`](../lab/brownfield/coexistence_gate.py), and the independent negative tests are [`test_coexistence_gate.py`](../lab/brownfield/test_coexistence_gate.py).

1. A stable `operationId` and full fingerprint classify a replay as duplicate, conflict, in-flight or ambiguous. A timeout does not prove a rollback.
2. A proposed cutover must drain in-flight requests and resolve every `UNKNOWN` by independent durable observation. A reconciliation assertion without underlying records is **not proof**.
3. Compare *balances, operations, postings and outbox* independently, plus operation counts and a monotonically observed watermark. Equality of two manually supplied digests is only a **synthetic input assertion**.
4. A successful **simulated** transition changes the single in-memory writer and increments its epoch. Stale-epoch requests are refused. Actual distributed fencing requires an atomically persisted authority and enforcement at **every** write entry point, including batch and branch/offline channels.
5. A rollback is a **new migration**, not a configuration toggle. If the candidate has committed new transfers, the legacy side must be caught up and independently reconciled before it can safely become authoritative again.

The synthetic rehearsal deliberately keeps `TODM G6 = BLOCK`. Its G5-style negative tests do not constitute verified PostgreSQL behavior, a customer-approved Golden Master, a signed policy baseline or permission to release.

## Required durable experiment — not yet demonstrated by this slice

Create a disposable PostgreSQL 16 instance and .NET 10/Npgsql 10.x replacement, reusing **ideas** from E1 rather than modifying archived E1 evidence. Put stable operation IDs, debit/credit, two postings, outbox and a database-enforced writer epoch behind one atomic transaction. A read path for CAP-005 must distinguish **booked balance** from **available funds** and reject a stale projection version; it must not invent holds or customer mandates.

Demonstrate SIGKILL before COMMIT, process termination after COMMIT but before reply, replay and independent persisted SQL inspection. Record original source SHA, runner, PostgreSQL image digest, timings and both positive and negative results. Confirm that the candidate is read-only before promotion, and that rollback is blocked on an unresolved operation, state divergence or an outdated authority epoch.

## Golden Master, TODM and ownership

The Golden Master characterizes what the incumbent system does. It may expose anomalous, obsolete or incorrect behavior; it is **not automatically binding business truth**. The accountable business owner approves intended behavior and exceptions, while a separately qualified TODM oracle checks those decisions. Until baseline approval, qualified independence and explicit human G6 authorization exist, the verdict remains **BLOCK / NOT PRODUCTION APPROVED**.

**Scope limit:** none of the rehearsal results proves bank-grade authentication, real financial reconciliation, HA, IBM Z MIPS equivalence, p99 under production traffic or regulatory acceptance. E2 Orleans capacity and F10 topology have separate independent acceptance gates.
