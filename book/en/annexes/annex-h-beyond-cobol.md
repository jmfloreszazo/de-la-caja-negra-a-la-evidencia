**English** · [Español](../../es/anexos/anexo-h-mas-alla-de-cobol.md)

[← Annex G · Sources and scope of the research](annex-g-sources-and-scope-of-the-research.md) · [Contents](../README.md) · [Annex I · Evidence campaigns →](annex-i-evidence-campaigns-and-limits.md)

# Annex H · Beyond COBOL

## What travels with the method

COBOL gives this book concrete problems, not an exclusive jurisdiction. A Java service, a VB6 application or an RPG batch can also conceal rules, depend on undocumented interfaces and disagree with its replacement. The transferable question is not “can this language be translated?” but “which observable behaviour must survive, who accepts it, and what evidence could contradict the candidate?”

The [oracle methodology in Chapter 10](../part-3-oracles/10-todm-and-the-problem-of-accepting-what-we-build.md) applies without requiring a particular implementation language: recover evidence, establish an independently approved baseline, qualify the evaluator, bind observations to the candidate and separate technical acceptance from release authority. The golden master records what happened; it does not automatically decide what should happen. An approved correction must remain visible as an intentional difference.

What does not travel automatically is the implementation of that method. A COBOL parser does not become a PL/I parser; a JSON comparison does not capture a GUI, a memory-mapped device or a distributed commit. Each new boundary needs an observation adapter, trusted expectations and negative controls. A method can be portable while every adapter remains specific.

## Applicability matrix: contracts before syntax

The following rows are **assessment guidance**, not a catalog of executed migrations or certified adapters. Grouping languages saves space; it does not make their semantics equivalent.

| Language or environment | What can be reused | What must be specified and verified anew |
|---|---|---|
| Java / C# | Capability contracts, independent examples, state and ledger invariants, failure scenarios | Decimal representation and rounding; integer overflow; exceptions and nullability; JVM/CLR versions, libraries, JIT and garbage collection; transaction propagation |
| VB6 / VB.NET | Approved user-visible outcomes, event traces, reference comparisons | Distinguish the two runtimes; `Variant`, `Empty` and `Null`, coercions, locale and date conversion; COM lifetime, UI event order and database provider behaviour |
| RPG / IBM i | Business capabilities, batch reconciliation, single-writer and cutover criteria | Decimal fields, CCSID, indicators, record access, job state, commitment control and journal boundaries; installed dialect and platform |
| PL/I | Rules, boundary cases, independent expected results, transaction invariants | Fixed/binary precision, condition handling, storage layout, compiler options and linkage; host services and database integration |
| C / C++ | Protocol contracts, state machines, differential and property tests | Width, signedness, ownership, ABI, alignment, endianness, concurrency and undefined behaviour; compiler, optimization and native dependencies |
| Python / JavaScript | Oracle separation, explicit cases, schema checks and negative controls | Dynamic coercion and missing values; Python decimal context and native extensions; JavaScript `Number`/`BigInt`; serialization, asynchronous scheduling and dependency versions |
| Embedded / real-time systems | Requirements traceability, state invariants, fault scenarios and independent acceptance | Hardware, interrupts, deadlines, resource budgets, reset and power-loss behaviour; hardware-in-the-loop evidence and any required safety assurance |

A row can apply to an upgrade within the same language as well as a rewrite. Replacing a compiler, database driver or runtime may change observable behaviour without changing the source. Record the complete execution environment, not merely the language name.

## Semantic boundaries that need their own oracle

**Numbers.** Specify precision, scale, rounding mode and the point at which rounding occurs. Decimal arithmetic is not interchangeable with binary floating point. Define intermediate as well as final ranges: Java integer wrapping, C# checked or unchecked arithmetic, Python integers and JavaScript numeric representations do not offer the same overflow contract. Test negative values, midpoints, maximum magnitudes and serialization. A matching display can hide a different stored amount.

**Text and absence.** Encoding, normalization, collation, padding and byte length are separate decisions. The [EBCDIC exercise](../../../lab/examples/ebcdic-boundaries/README.md) illustrates why a successful round trip can still preserve the wrong meaning; it does not validate every host code page. Preserve the distinction between absent fields, null, empty strings, zero and sentinel values when the domain makes that distinction. An adapter that silently trims or defaults data can manufacture agreement.

**Dates and time.** Define calendar, precision, time zone, offset, daylight-saving transitions, business date and cut-off policy. A local timestamp is not necessarily an instant. Freeze or control the clock where appropriate, and include ambiguous and nonexistent local times. Reference fixtures must not accidentally depend on the evaluator's locale or today's date.

**Concurrency and transactions.** Specify observable histories, idempotency, ordering and the durability point. A mutex, event loop, actor or language transaction annotation does not by itself establish the business commit boundary. Test duplicates, cancellation, lost replies and crashes on either side of commit; inspect persisted state independently. Carry the reasoning from the [verifiable architecture](../part-3-oracles/11-the-architecture-of-a-verifiable-modernization.md), not an assumption that a familiar threading API preserves it.

**FFI and undefined behaviour.** At a foreign-function interface, verify calling convention, field layout, ownership, error propagation and lifetime. For C/C++, undefined behaviour has no stable language-level result to preserve. A repeatable legacy observation can inform an explicitly scoped compatibility requirement, but cannot turn undefined behaviour into a portable specification. Use suitable diagnostics and redesign the boundary; do not label one successful differential run a proof.

## Decision models express rules, not translations

BPMN can describe process order, events and responsibilities; DMN can express decisions and rule tables. Neither translates arbitrary source code into approved business meaning. A diagram extracted from a program remains a hypothesis until its interpretation and authority are established.

For an executable oracle, document the supported semantic subset: input types, missing-value handling, comparisons, rule priority or hit policy, defaults, errors and relevant state transitions. Bind model versions and evaluator versions to the evidence. An unsupported construct must block or remain inconclusive, not be ignored. The [decision-model lab](../../../lab/decision_models/README.md) supplies its own scope and reproduction instructions; a limited verifier is not a complete or certified BPMN/DMN engine. Model notation alone establishes neither conformance nor approval.

## ADRs preserve the baseline and its rationale

The [architecture decisions in Annex D](annex-d-architecture-decisions.md) remain useful beyond COBOL. For each new language boundary, record the existing behaviour, business authority, chosen contract, rejected alternatives and rationale. Include uncertainties, compatibility exceptions, owner, review trigger and exit criteria. An ADR explains why the baseline was selected; it does not replace executable cases or grant approval by being committed.

A practical acceptance package should contain:

1. A bounded capability and interface contract, including failure outcomes; use the [lab contract](annex-b-lab-contract.md) and [meaning-focused comparison](../part-3-oracles/12-cobol-and-c-must-agree-on-meaning.md) as examples, not universal schemas.
2. Separately governed expected results, authorized reference observations and explicit intentional differences.
3. Qualified adapters and evaluators, with clean controls, defective candidates and incomplete evidence.
4. Candidate, model, dependency and runtime identities, raw observations and original execution provenance.
5. A scoped verdict, unresolved limitations, independent release authority and a controlled baseline-change process.

## What the available tools actually establish

The [practical TODM adapter](../../../lab/todm_validation/README.md) validates specified evidence shapes and pinned governance semantics. It is not a universal runner for these languages or a production authorization service. The [decomposition lab](../../../lab/decomposition/README.md) checks synthetic boundary hypotheses; it does not discover arbitrary source dependencies. The [three-way commission exercise](../../../lab/examples/commission-three-way/README.md) demonstrates a concrete reference/candidate/expectation arrangement, not cross-language certification.

This annex adds no executions. Existing COBOL, C#/.NET and Python artifacts retain their documented scopes; citations to other languages or platforms are not measurements of them. Local smoke tests do not become Azure measurements, and Azure experiments do not establish mainframe equivalence. A new language, runtime or workload needs its own retained evidence. The portable contribution is the discipline of making that requirement explicit, not a promise that the necessary proof already exists.

---

[← Annex G · Sources and scope of the research](annex-g-sources-and-scope-of-the-research.md) · [Contents](../README.md) · [Annex I · Evidence campaigns →](annex-i-evidence-campaigns-and-limits.md)
