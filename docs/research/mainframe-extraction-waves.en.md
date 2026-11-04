# Brownfield extraction waves from observed business capabilities

**Issue #32 · Research and test protocol · 4 November 2026.** [Español](mainframe-extraction-waves.es.md). This is a synthetic, falsifiable method for **staging replacement of an incumbent system**, not a source-code parser, automatic DDD service generator, production bank study or capability acceptance. Use together with [the 30 functional hypotheses](../../lab/decomposition/functional_capabilities.json), the [functional evidence gate](../../lab/decomposition/functional_contract_gate.py), and [the independent graph oracle](../../lab/decomposition/oracle.py).

## The unit of migration is a business promise, not a COBOL program

Event Storming may reveal commands, decisions, reversals, reports and end-of-day timings; strategic DDD proposes bounded contexts; runtime observation and source-application owners must falsify or validate the hypotheses. **Event Storming is not Event Sourcing.** A static call, Db2 table or JCL job is not automatically a domain boundary. A new .NET 10 component is still a **brownfield** replacement because the current estate, operations, customer interfaces and data authority already exist.

There are three separate decisions, none implied by the previous one:

1. **Functional discovery:** what does the current system appear to do, what should it do, and who may approve those rules? All 30 sample records remain `HYPOTHESIS_NOT_OBSERVED`.
2. **Structural feasibility:** does the proposed extraction cross an indivisible financial write unit, batch cutoff, unknown dependency or external effect? An initial graph can only refute unsafe hypotheses, not prove completeness.
3. **Operational/business authority:** can the incumbent writer be fenced, existing operations/UNKNOWN states reconciled, cutover and rollback governed, quantitative capacity recovered and the independent TODM oracle approved? **Never granted by graph scoring.**

## Tested decision types and contracts

| Type | Intended extraction | Nonnegotiable boundary |
| --- | --- | --- |
| `READ_ONLY_PROJECTION` | Read-model capability with a new projection, mainframe remaining authoritative | No new financial writes, watermark, rebuild/idempotency, nonauthoritative data classification and source-of-truth fallback; never use a stale projection for ATM cash authorization |
| `EXPOSE_LEGACY` | New API/ACL/channel façade on an existing core | Legacy retains all writer authority; a façade alone does not block direct CICS/IMS/batch/offline/privileged paths |
| `COMMAND_REPLACEMENT` | Replacement command with durable owner/fence | Reject a boundary crossing the same atomic ledger unit, batch restart/cutoff, unexplained external effect or financial reconciliation consumer |
| `RETIRE` | Decommission a genuinely unused route/job | Reject any declared consumers, unknown seasonal/late paths, unreconciled writes, batch cutoff or external effects; absence from one sampled trace is not evidence of absence |

A `CANDIDATE_ONLY` structural decision does **not** imply that missing static/runtime edges have been observed, that all business requirements are correct, that a chosen pattern is optimal, or that cutover is authorized. Neither `CANDIDATE_ONLY` nor a manually filled catalog can make TODM G2/G6 PASS.

## Four reproducible synthetic waves

The [fixture](../../lab/decomposition/wave_fixture.json) links functional CAP IDs, typed hypothetical dependencies and explicit questions to ask the real system owner. **Edges are hypotheses, not captured mainframe traces**.

| Proposed wave | Business hypothesis | Expected structural decision | Reason |
| --- | --- | --- | --- |
| **W01** balance inquiry `CAP-005` | Build a read-only balance projection while the incumbent remains authoritative | **CANDIDATE_ONLY** | Only with explicit watermark, consistent-source fallback, idempotent rebuild, nonauthoritative designation and no financial effects. **Booked vs available and ATM authorization remain distinct** |
| **W02** internal transfer `CAP-007` | Move only the transfer command to the candidate | **REJECT** | A hypothesized atomic ledger relation with `CAP-019` would be split; one new service per program breaks the original financial promise |
| **W03** scheduler `CAP-021` | Retire the old scheduler before replacement | **REJECT** | The period-close dependency to `CAP-020` crosses the boundary and the seasonal/backdated `CAP-022` dependency is explicitly UNKNOWN |
| **W04** branch operations `CAP-027` | Expose a branch façade and leave legacy data/write authority intact | **CANDIDATE_ONLY** | An ACL/strangler entry point can be a useful seam but cannot validate offline messages, privileges, security or latency without external evidence |

The fixture also hypothesizes dependencies from ATM authorization to cash-dispense reconciliation, ledger to file reconciliation and close to GL. None asserts a particular bank uses such paths. For W02, a saga or Orleans grain **cannot** be presumed to replace the ACID guarantee. For W03, replacing JCL with a timer does not establish restart/checkpoint and accounting-calendar semantics.

### Run the independent structural controls

```bash
python3 -m unittest discover -s lab/decomposition -p 'test_*.py' -v
python3 lab/decomposition/wave_gate.py \
  lab/decomposition/functional_capabilities.json \
  lab/decomposition/wave_fixture.json
# Expected exit 1: W02/W03 rejected. This is a correct negative experiment,
# not a failed test runner or evidence of production deployment.
```

The new tests deliberately falsify boundaries by omitting projection freshness/fallback, turning a read projection into a writer, splitting the atomic group, crossing the ATM external-effect edge, retiring a scheduler despite unknown seasonal activity, forging approval metadata and violating the declared dependency/wave schema. The gate returns `INVALID` (exit 2) for malformed input, exit 1 for rejected structural proposals and exit 0 only when **all** structural proposals are candidates; that exit 0 is **never a business PASS**.

## How to pick real extraction waves without fake precision

Do not assign numerical scores to unknown contract data. Use a **gated decision register** with fields for: capability and named business owner; approved versus observed Golden Master; entry points across online/batch/async/branch; source-of-truth and writer sets; same-transaction/commit boundary; event ordering and cutoff times; data watermark; downstream consumers and external effects; unknown runtime edges; volume, hot keys and latency; effective RPO/RTO; coexistence cost; roll-forward/rollback constraints; negative scenario and independent oracle references.

**Wave 0 — keep/observe:** inventory real transactions, batch windows, data authorities and disputed policy; instrument without giving the candidate write authority.

**Wave 1 — expose or project:** make legacy-owned calls safer through versioned ACLs and measured read models. Do not turn projected balances into spendable funds; design rebuild, lag alarm, access control and direct-source fallback.

**Wave 2 — replace an isolated behavior:** move one behavior only after approved business contract, durable source-side fence, in-flight/UNKNOWN reconciliation and falsifiable golden-baseline oracle. A modular monolith may offer better transactional safety than multiple microservices.

**Wave 3 — transfer ledger or settlement authority:** only if paired postings, outbox, batch/GL and external payment/cash effects are proved together. Hold the whole atomic unit or explicitly negotiate different, owner-approved consistency guarantees. An unsupported distributed saga is not an escape hatch.

**Wave 4 — decommission:** verify zero effective writers/consumers for online, seasonal, offline and privileged paths across a justified observation window; validate records retention, archival, recovery and removal of obsolete permissions. Unknown routes => retain and investigate.

Each wave must have a preregistered refusal condition and an independent decision: `RETAIN`, `EXPOSE`, `REPLACE`, `RETIRE`, or `INCONCLUSIVE`. A possible next infrastructure target (on-prem, Azure, hybrid, modular monolith or Orleans) is a **design choice**, not the definition of a business context.

## Executable bounded W01 follow-up

The [W01 synthetic PostgreSQL read-projection experiment](w01-projection.en.md) extends the proposed read-only seam with real SQL snapshots, watermark, digest, fallback and negative controls. It is **not** a CDC pipeline, physically independent HA, a real mainframe read contract or a substitute for the #58 incumbent fence. The original graph proposal remains CANDIDATE_ONLY.

## Status and next evidence requirements

**Delivered by this increment:** an executable and auditable **synthetic wave screen**, four proposed slices, explicit cross-capability constraints, adverse tests and ES/EN research. This does not revise the 30 historical hypotheses into real bank requirements.

**Not delivered:** authorized source/platform traces, a customer-approved Golden Master and process calendar, runtime dependency completeness, source-side fencing, external payment reconciliation, measured production-level load/HA, or TODM G2/G6 approval. Issue [#32](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/32) is now **CLOSED / completed for the research and synthetic-method deliverable**; external bank/source validation is still **OPEN in #58**. [Brownfield real source-authority acceptance](../BROWNFIELD_SOURCE_FENCE.md) defines the separate owner-controlled proof; [E2 technical PASS prerequisites](../E2_FULL_PASS_PROTOCOL.md) remain independent and **do not** authorize book publication or a bank migration.
