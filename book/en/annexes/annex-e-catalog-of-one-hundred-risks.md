**English** · [Español](../../es/anexos/anexo-e-catalogo-de-cien-riesgos.md)

[← Annex D · Architecture decisions](annex-d-architecture-decisions.md) · [Contents](../README.md) · [Annex F · Operational glossary →](annex-f-operational-glossary.md)

# Annex E · Catalog of one hundred risks

The numbering identifies each risk; it does not express frequency, severity or priority. Each row proposes an application option, an infrastructure capability and the evidence that could refute them. The lab includes the same catalog in JSON and Markdown, with the owner and evidence fields empty so it can be used in a real assessment.

## Data and representations

Main scope of this family: COBOL and formats. Infrastructure measures require the contract of the chosen engine or service.

| ID and risk | Application option | Infrastructure option | Evidence to demand |
|---|---|---|---|
| R001 Non-numeric data in numeric fields | Boundary validation and quarantine | Keep originals and rejections | Inject invalid bytes and check rejection |
| R002 Incompatible packed decimal and sign | Explicit COMP-3 codec | Binary staging with versioned schema | Compare bytes, sign, scale and extremes |
| R003 Zoned decimal sign misread | DISPLAY representation adapter | Traceable conversion per dataset | Test signs and source variants |
| R004 Shared memory through REDEFINES | Layout model and discriminated union where applicable | Version copybook and codec | Check every view of the same block |
| R005 OCCURS DEPENDING ON loses length | Collection with validated cardinality | Store length and version | Test zero, maximum and invalid length |
| R006 BY REFERENCE parameters lose aliasing | Call adapter with explicit ownership | Inventory of binary contracts | Observe shared mutation across calls |
| R007 Padding spaces change comparisons | Field type with explicit policy | Keep raw value during transition | Compare blanks, length and empty strings |
| R008 EBCDIC order changes when sorting Unicode | Defined comparer and collation | Staging with identified CCSID | Compare key sequences and ties |
| R009 Byte length confused with character length | Separate binary buffer from text | Encoding metadata per interface | Test accents, lengths and truncation |
| R010 Compiler options change results | Semantic profile per toolchain | Reproducible build with pinned versions | Run corpus with documented options |

## Money and time calculations

Main scope of this family: Business semantics. Infrastructure measures require the contract of the chosen engine or service.

| ID and risk | Application option | Infrastructure option | Evidence to demand |
|---|---|---|---|
| R011 PICTURE range exceeds target type | Domain type with explicit range | Schema with precision and constraints | Test minimum, maximum and overflow |
| R012 Rounding follows a different rule | Rounding policy per operation | Version approved rules | Test ties and adjacent values |
| R013 Rounding partial results changes the total | Calculation pipeline with defined stages | Keep permitted calculation trace | Compare partials and final aggregate |
| R014 Negative amounts carry other semantics | Types for reversal, debit and credit | Constraints per movement type | Test negatives, zero and reversals |
| R015 Mixed currencies in one balance | Money with currency and scale | Partitions and indexes per currency when appropriate | Reject aggregates across currencies |
| R016 Business date uses server date | Injected business clock | Versioned calendar and time zone | Replay closings with a controlled clock |
| R017 Abbreviated dates hide pivots | Explicit calendar adapter | Keep original date and rule | Test century change and leap years |
| R018 Zero, spaces and NULL are confused | Explicit absence model | Reversible migration and constraints | Check the three values separately |
| R019 Rate table changes during a batch | Rule snapshot per run | Configuration with validity and version | Replay batch with the same rule |
| R020 Division by zero alters the flow | Typed result and exception policy | Log errors without losing input | Test zero divisor and later state |

## Program flow and state

Main scope of this family: COBOL and design. Infrastructure measures require the contract of the chosen engine or service.

| ID and risk | Application option | Infrastructure option | Evidence to demand |
|---|---|---|---|
| R021 GO TO hides business paths | Control graph and gradual refactoring | Static tools with provenance | Cover branches before and after the change |
| R022 PERFORM or paragraphs depend on fall-through | Function extraction with explicit boundaries | Baseline of executed paths | Compare execution order and effects |
| R023 Reused variable mixes concepts | Typed contexts and domain names | Read/write traceability | Run sequences that reuse storage |
| R024 Dynamic CALL missing from dependencies | Dispatch registry and adapters | Inventory of loaded modules and versions | Test every target and an unknown target |
| R025 WORKING-STORAGE keeps state between calls | Explicit state per session or entity | Temporal affinity only when justified | Compare two invocations in sequence |
| R026 Non-reentrant routine receives parallel requests | Per-invocation context or bounded serialization | Isolate legacy runtime workers | Force concurrent calls to the same module |
| R027 Uninitialized value looks stable | Initialization and valid-value contract | Compiler diagnostics during discovery | Repeat with different initial state |
| R028 Apparently dead code has consumers | Reachability analysis and gradual retirement | Usage telemetry and observation window | Cover rare paths before deleting |
| R029 Return code becomes a generic exception | Explicit map of errors and decisions | Metrics per result class | Compare return, effect and recovery |
| R030 Duplicated rule evolves differently | Domain module or versioned table | Rule ownership and coordinated deployment | Check every consumer of the rule |

## Files and datasets

Main scope of this family: Mainframe environment. Infrastructure measures require the contract of the chosen engine or service.

| ID and risk | Application option | Infrastructure option | Evidence to demand |
|---|---|---|---|
| R031 VSAM KSDS access loses key semantics | Repository with explicit keys and traversals | Indexes and storage matched to access | Compare missing key, duplicate and ranges |
| R032 RBA or physical position used as identity | Stable identifier and mapping table | Keep mapping during migration | Verify references after reordering |
| R033 Variable records lose length metadata | Record codec with framing | Format and block manifest | Test limits, empty and truncated records |
| R034 Sequential restart repeats committed records | Checkpoint plus idempotent processing | Durable checkpoint next to agreed progress | Crash and resume at commit boundaries |
| R035 Two jobs write the same file | Write owner with fencing | Lease verified by the target | Simulate old owner after handover |
| R036 Consumer reads a file still being written | Publication with completeness manifest | Immutable objects and final marker | Interrupt upload and forbid partial consumption |
| R037 Whole dataset loaded into memory | Streaming and bounded batches | Memory limits and temporary storage | Process volume larger than the working set |
| R038 SORT/MERGE changes order or stability | External sort and tie-break contract | Sized, recoverable temporary disk | Compare repeated keys and totals |
| R039 Sequential read becomes random access | Block or stable-range access | Indexes and layout matched to the traversal | Compare order, completeness and I/O cost |
| R040 Spool or report loses contractual format | Rendering service with versioned template | Output archive with defined retention | Compare content, pagination and consumers |

## Database access

Main scope of this family: Data and concurrency. Infrastructure measures require the contract of the chosen engine or service.

| ID and risk | Application option | Infrastructure option | Evidence to demand |
|---|---|---|---|
| R041 CICS/Db2 unit of work split into calls | Explicit unit-of-work boundary | One transactional engine when viable | Crash between writes and check atomicity |
| R042 A cursor becomes N+1 queries | Set operations and batching | Indexes and round-trip budget | Measure queries per operation and p99 |
| R043 Balance query lacks a selective index | Access model and query tuning | Indexes based on measured plans | Compare plans with representative volume |
| R044 NULL and spaces alter SQL predicates | Semantic translation layer | Target schema with explicit rules | Compare filters, joins and aggregates |
| R045 Read-check-update allows races | Conditional update or version check | Constraints and transaction in the engine | Launch incompatible debits in parallel |
| R046 Global predicate suffers write skew | Isolation or locking that covers the invariant | Design indexes and consistency boundaries | Test concurrent histories over several rows |
| R047 Transaction waits on network or a human | Shrink critical section and move preparation out | Transaction timeouts and observability | Force a slow dependency and measure locks |
| R048 Variable lock order creates deadlocks | Consistent order and bounded full retry | Collect engine graphs and victims | Force a cycle and check recovery |
| R049 Lock wait consumes the whole budget | Deadline and bounded admission | Timeouts aligned across layers | Hold a lock and verify bounded exit |
| R050 Read replica shows a stale balance | Read-your-commit with required consistency | Read routing by criticality | Read after commit and during lag |

## Transactions and financial messaging

Main scope of this family: Business guarantees. Infrastructure measures require the contract of the chosen engine or service.

| ID and risk | Application option | Infrastructure option | Evidence to demand |
|---|---|---|---|
| R051 Commit happens but the response is lost | Operation identity and result lookup | Durable decision log | Resend after commit without response |
| R052 Idempotency key reused with another mandate | Compare mandate identity and content | Uniqueness and decision retention | Reject same ID with a different amount |
| R053 Change and event stored separately | Transactional outbox | Store intent in the same transaction | Crash between commit and publication |
| R054 Redelivered event repeats its effect | Inbox or idempotent consumer | Persist deduplication with the effect | Redeliver and count confirmed effects |
| R055 Commit spans different resource managers | Keep compatible coordination or redraw the boundary | Recoverable coordinator and participants | Test prepared states and recovery |
| R056 Compensation replaces atomicity without approval | Choose transaction or saga by contract | Durable workflow and reconciliation | Observe permitted intermediate states |
| R057 Reservation expires without releasing funds | Reservation state machine | Persistence, timers and reconciliation | Crash on expiry, confirm and release |
| R058 Concurrency allows overdraft | Invariant in the engine and conditional debit | Transaction and balance constraint | Compete for a balance insufficient for both |
| R059 Stale owner keeps writing | Fencing with epoch validated at the target | Write authority and monotonic token | Revive old owner and reject its writes |
| R060 Balance and postings stop matching | Immutable ledger and reconcilable projection | Durable history and per-operation indexes | Recompute balances and per-movement balance |

## Batch and scheduling

Main scope of this family: Mainframe operations. Infrastructure measures require the contract of the chosen engine or service.

| ID and risk | Application option | Infrastructure option | Evidence to demand |
|---|---|---|---|
| R061 JCL hides dependencies between jobs | DAG with declared inputs and outputs | Scheduler with durable history | Reproduce order and preconditions |
| R062 Return codes drive undocumented branches | Workflow with explicit decisions | Log of codes and transitions | Test each branch and an unexpected exit |
| R063 Batch restart re-applies movements | Idempotent chunk with checkpoint | Persist progress and dataset version | Restart before and after each commit |
| R064 GDG generations mixed up when moved | Dataset identity per generation | Versioned objects and batch manifest | Reprocess one generation without mixing another |
| R065 Batch window depends on a serial step | Optimize the critical path before scaling | Resources reserved per phase | Measure the full DAG and the deadline |
| R066 One batch partition concentrates the work | Cost-based partitioning and safe work stealing | Per-partition metrics and worker limits | Inject skew and measure maximum duration |
| R067 Commit size maximizes locks or rework | Chunk with defined atomicity | Sized log and checkpoints | Measure lock time and lost work |
| R068 Batch steals resources from interactive traffic | Bulkheads and explicit priorities | Pools, quotas and separate capacity | Run a mixed batch and online load |
| R069 Closing calendar differs across platforms | Versioned business calendar | Service or configuration with validity | Test holidays, time zone and day change |
| R070 Cancelling a job leaves untraceable work | Cooperative cancellation and resumption | Durable state and worker draining | Cancel at every stage and reconcile |

## Integration and coexistence

Main scope of this family: Contracts and systems. Infrastructure measures require the contract of the chosen engine or service.

| ID and risk | Application option | Infrastructure option | Evidence to demand |
|---|---|---|---|
| R071 COMMAREA exposed as a DTO without a contract | Anti-corruption layer with versioned schema | Gateway and payload limits | Compare layout, ranges and responses |
| R072 Message exceeds transport limit | Payload reference with integrity | Durable object with temporary access | Test expiry, size and integrity |
| R073 Encoding converted twice | Single codec at a defined boundary | Conversion and origin metadata | Round-trip representative characters |
| R074 MQ acknowledgement decoupled from business effect | Receive protocol and idempotent effect | Transaction manager or inbox by scope | Crash before and after acknowledgement |
| R075 Operations for one entity arrive out of order | Business sequence and per-key consumer | Sessions or partitions plus durable state | Send out of order and detect gaps |
| R076 Poison message blocks a whole entity | Quarantine with resolution policy | DLQ, metrics and controlled resumption | Verify continuity without skipping critical rules |
| R077 Retries in several layers amplify load | A single retry budget with jitter | Admission limits and circuit breaker | Cut a dependency and measure amplification |
| R078 Slow external dependency holds the whole pool | Bulkhead and timeout per dependency | Isolated pools and reserve capacity | Saturate one target and observe the others |
| R079 Screen keeps hidden conversational state | Explicit session or workflow state | Persistence and expiry by contract | Resume a session after an instance change |
| R080 Technical identity replaces business permissions | Authorization context and least privilege | Workload identity and verified policies | Test allowed and denied access |

## Performance and capacity

Main scope of this family: Application and infrastructure. Infrastructure measures require the contract of the chosen engine or service.

| ID and risk | Application option | Infrastructure option | Evidence to demand |
|---|---|---|---|
| R081 MIPS converted directly to vCPU | Demand model per transaction | Tested hardware candidates | Replay the mix with equivalent durability |
| R082 Per-record allocations trigger the GC | Streaming and measured allocation reduction | Memory budget and GC telemetry | Measure pauses at target volume |
| R083 Synchronous waits exhaust the ThreadPool | End-to-end async where it applies | Instrument queue and available threads | Force slow I/O and observe latency |
| R084 More workers increase conflicts and CPU | Concurrency limited by resource | Measured pools and limits | Concurrency sweep with errors and p99 |
| R085 Unbounded queue hides a service outage | Backpressure and explicit rejection | Durable queue with capacity and alarms | Sustain a rate above consumption and drain |
| R086 Fast disk capped by the VM | Complete I/O model | Verify VM, disk and network limits | Measure IOPS, bandwidth and queues |
| R087 Log or synchronous replica dominates commit | Reduce work and group only when valid | Storage and replica with a durable contract | Measure commits with replica and failure |
| R088 Hot actor imposes a serial ceiling | Shrink critical section or revisit the aggregate | Spread other keys and observe queues | Concentrate load on a single identity |
| R089 Warm-cache-only test misleads | Cold and warm test design | Representative dataset and memory | Measure startup, warm-up and steady state |
| R090 Microservices multiply network round trips | Right-grained operations and locality | Place compute and data by latency | Count round trips and measure on a real network |

## SDLC, recovery and governance

Main scope of this family: Engineering and operations. Infrastructure measures require the contract of the chosen engine or service.

| ID and risk | Application option | Infrastructure option | Evidence to demand |
|---|---|---|---|
| R091 Nobody knows which version is in production | Artifact inventory and manifest | Traceable build and deployment | Reconcile binaries, configuration and hashes |
| R092 Runtime change alters behaviour | Pinned dependencies and differential regression | Verified images and upgrade plan | Replay corpus when the toolchain changes |
| R093 Incident cannot be reconstructed | Correlated traces and business events | Durable telemetry with data minimization | Follow one operation across all components |
| R094 High availability lacks proven recovery | Failure design and reconciliation | Rehearsed replicas, backups and restore | Measure RTO, RPO and consistency under load |
| R095 New schema prevents running the previous version | Expand/contract and reader compatibility | Versioned schema migration | Rehearse coexistence and cross reads |
| R096 Code rollback does not revert data or events | Return plan with repair or compensation | Snapshots and log of applied decisions | Rehearse return after real writes |
| R097 Shutdown cuts in-flight operations | Graceful shutdown and bounded draining | Probes and coordinated termination | Kill a worker during a commit |
| R098 Shared credentials widen the blast radius | Per-service identity and explicit authorization | Secret store or managed identity per environment | Rotate, revoke and check effective denial |
| R099 A different artifact is delivered than the one verified | Approval bound to digest and scope | Protected repository and immutable promotion | Swap the artifact and block delivery |
| R100 Every test inherits the same false assumption | Independent oracle and qualification | Protected baseline and controlled verifier | Seed a common fault and check rejection |

---

[← Annex D · Architecture decisions](annex-d-architecture-decisions.md) · [Contents](../README.md) · [Annex F · Operational glossary →](annex-f-operational-glossary.md)
