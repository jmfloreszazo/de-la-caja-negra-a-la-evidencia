# Book roadmap — next releases

**English** · [Español](TODO.es.md)

Owner and editorial authority: **José María Flores Zazo · [jmfloreszazo.com](https://jmfloreszazo.com)**.
Planning date: **8 November 2026**. Published baseline: **v2026.11.08.1**.

> **Proposal, not execution evidence.** This checklist organizes future work; it does not authorize a deployment, release, customer access or scientific acceptance. Check a task only after retaining its verification. Release by fulfilled objectives, not by page count. Dates and version names are tentative.

This is the forward-looking plan. [ROADMAP.md](ROADMAP.md) remains the historical closed-edition record. Use the [experiment roadmap](docs/EXPERIMENT_ROADMAP.md) and [evidence matrix](docs/EVIDENCE.md) for executed results and their limits. This document does not reopen closed issues or reactivate frozen research.

## 1. Next editorial revision

**Goal:** finish and organize what already exists. Candidate version: `v2026.11.08.2`, subject to publication approval.

- [ ] Integrate the locally prepared sources-last change: Annex G always closes the book; preserve letters and navigate F → H → G in both editions. Verify its actual status before applying again.
- [ ] Reconcile the [post-relocation review](docs/reviews/2026-11-08-post-relocation/README.md) with current `main`; verifier fixes landed during publication, so do not repeat already resolved findings.
- [ ] Resolve remaining ambiguous Azure history and companion-chapter navigation; mark each finding fixed, accepted or deferred with a reason.
- [ ] Unify entry points for reading, running examples, verifying evidence and understanding limits.
- [ ] Visually inspect final CI PDFs: covers, indexes, added chapters, tables, listings, figures and final annex order.
- [ ] Write release notes stating changes, tests and unresolved limitations.

**Exit criterion:** both editions consistent, checks passing, published-candidate PDFs inspected, and no important editorial finding without an explicit disposition.

**Excluded:** new experiments, new frameworks or a general rewrite. This checklist does not publish this candidate version.

## 2. Independent reproduction release

**Goal:** another person can reproduce and challenge the book without our workstation.

- [ ] Validate the documented route from a clean clone: prerequisites, versions, commands, indicative duration and expected outcomes.
- [ ] Arrange authorized delivery of original evidence packages, with discoverable manifests and a separate backup. A hash does not provide the bytes.
- [ ] Separate historical verification from new execution; default verification must not overwrite records.
- [ ] Obtain a third-party reproduction report with environment, commands, failures and differences from the reference.
- [ ] Publish a support matrix distinguishing tool tests on Windows/macOS from execution of the complete laboratory.

**Exit criterion:** a third party reproduces the minimum documented route and verifies an evidence package; all deviations are retained and explained.

**Dependencies:** a deliverable baseline, distributable inputs and an independent participant. A second run by the same assistant is not independent reproduction.

## 3. One capability from beginning to end

**Goal:** connect the existing mechanisms into a complete, understandable modernization case.

- [ ] Select one small, representative, reversible capability: for example, a booked-balance query, explicitly distinct from available balance.
- [ ] Identify the business problem, scope, exclusions and accountable roles.
- [ ] Separate observed legacy behaviour from intended business policy.
- [ ] Connect vocabulary, decision/process models and ADRs to the capability.
- [ ] Establish the baseline and independent oracle, including negative and incomplete cases.
- [ ] Implement and evaluate the candidate against the frozen criteria.
- [ ] Exercise relevant integrations, data boundaries and external effects.
- [ ] Rehearse coexistence, reconciliation and cutover/reversal where applicable.
- [ ] Produce an outcome report: working, rejected, unknown and untested.

**Exit criterion:** the reader can trace one obligation from its definition to evidence of its verification, including failures.

**Dependency and classification:** a real pilot requires an identified system, authorized access and real accountable owners. Otherwise use public or synthetic inputs and say so. Do not invent customer approval or make COBOL parsing a prerequisite for every capability.

## 4. TODM applied to decisions and processes

**Goal:** teach how to maintain governed business truth, not merely draw models.

- [ ] Demonstrate overlapping decision rules, precedence and incomplete inputs using the supported DMN-inspired profile.
- [ ] Document a process with manual review, exception and resumption; distinguish illustrative steps from executable semantics.
- [ ] Trace a rule change through previous/new baseline, approval, tests and outcomes. Synthetic approval remains synthetic.
- [ ] Include an ADR recording a rejected alternative and its consequences.
- [ ] Contrast business `APPROVE`, technical verdict and production authorization.
- [ ] Demonstrate legacy and candidate agreement that nevertheless violates the independently specified rule.

**Exit criterion:** reproducible positive, negative and inconclusive cases, with traceability among rules, decisions and evidence.

**Excluded by default:** building full BPMN, DMN, CMMN, SBVR and OCL engines. If full semantics are needed, select an existing engine, justify it in an ADR and qualify the exact configuration. Reuse existing examples before adding duplicates.

## 5. Architecture under failures

**Goal:** extend single-host process faults into a precisely bounded distributed trial.

- [ ] Separate generator, services and database to match the declared hypothesis and failure domains.
- [ ] Preregister workload, durability, retry policy and recovery criteria.
- [ ] Execute open-loop load with the complete denominator: responses, failures, missed offers and ambiguous operations.
- [ ] Test instance loss and recovery; do not call process/instance loss physical-node loss without proof.
- [ ] Independently reconcile persisted operations and external effects after each fault.
- [ ] Retain configurations, observed costs, repetitions and statistical limitations.

**Exit criterion:** demonstrate a named recovery property on a recorded topology with an independent oracle.

**Dependencies:** authorized infrastructure, bounded spend, suitable load and real failure isolation. No valid mainframe comparison exists without a mainframe baseline and an equivalent approved contract. Such a comparison is not required to publish this bounded advance.

## 6. Comparative agent evaluation — E4

**Goal:** measure whether an independent oracle and its qualification improve outcomes.

| Arm | Evaluation |
|---|---|
| A | Tests produced alongside the candidate |
| B | Frozen independent oracle |
| C | Independent oracle with mutation qualification |

- [ ] Define tasks, budgets, selection, stopping rules and scoring before execution.
- [ ] Establish independently adjudicated defects and expected outcomes.
- [ ] Run comparable arms without leaking reserved cases into construction or repair.
- [ ] Record accepted defects, false rejections, inconclusives, attempts, tokens and costs.
- [ ] Measure actual human-review time and cost per accepted change; do not fill unknown fields with guesses.
- [ ] Analyse by task with justified uncertainty; retain failed and inconclusive runs.

**Exit criterion:** prior protocol, justified task set, complete observations and conclusions proportional to uncertainty. Replay of one candidate is not a new inference or independent task.

**Dependencies:** independent adjudication, reviewers and an authorized model budget. Neither a green test nor a synthetic mandate supplies G2/G6 business authority.

## 7. Beyond COBOL, supported by execution

**Goal:** turn part of Annex H into a concrete cross-language demonstration.

- [ ] Choose one additional language/runtime, not ten.
- [ ] Keep the capability and observable contract equivalent.
- [ ] Exercise real differences in decimals, overflow, dates, encoding or concurrency.
- [ ] Implement the necessary adapter and reuse the oracle only where its assumptions remain valid.
- [ ] Include a defect detected in the new runtime by the independent contract.
- [ ] Explain what was reusable and what required a new design.

**Exit criterion:** retained, reproducible execution in both environments. Do not extrapolate a single case to every system written in either language.

**Dependencies:** a stable capability contract and a suitable runtime. Initial runtime-boundary examples can precede the full comparative E4 study; not every item is a strict prerequisite for the next.

## Recommended priority and common publication gate

**Editorial closeout → independent reproduction → complete capability → applied TODM → distributed failures → comparative E4 → second-language evidence.** This is priority order, not a claim that all stages must finish before any release. Each delivery answers one question and lists the questions still open.

For every release:

- [ ] Spanish and English complete and synchronized; sources/scope Annex G last.
- [ ] CI for the published commit passes, with skipped jobs explicitly justified.
- [ ] Original evidence and failed attempts preserved; backup and distribution conditions documented.
- [ ] Actual public PDFs checked, not only local previews.
- [ ] Release notes include reproducibility requirements and limitations.
- [ ] No synthetic result promoted to business approval, capacity equivalence or production acceptance.
- [ ] Author explicitly authorizes publication, version and merge; no automatic release from this plan.

**Next recommended investment:** finish the editorial revision and obtain independent reproduction before adding more tools or chapters. A real customer pilot is separate work with its own access and approval boundaries.
