**English** · [Español](../../es/parte-7-organizacion/37-el-nuevo-contrato-de-modernizacion.md)

[← Chapter 36 · A hundred risks for choosing patterns with judgement](36-a-hundred-risks-for-choosing-patterns-with-judgement.md) · [Contents](../README.md) · [Epilogue →](../epilogue.md)

# Chapter 37 · The new modernization contract

> [!IMPORTANT]
> **Chapter thesis.** Before moving a COBOL capability, any technical leader should be able to sign seven clauses, and each one should be demonstrable with a concrete artifact.

To close, I propose a simple contract that any technical leader should be able to sign before moving a COBOL capability. **First**: we have identifiable evidence of what the system does. **Second**: its invariants and exceptions are recorded in an approved baseline. **Third**: we know which old responsibilities need a new mechanism and why. **Fourth**: implementations are subjected to independent oracles, including concurrency and failures. **Fifth**: the selected environment passes a realistic load test, with documented cost and capacity. **Sixth**: there is a controlled transition of data ownership, support and recovery. **Seventh**: we know which part of the legacy we retire and how we will verify it is no longer needed.

AI-assisted engineering radically changes the speed at which we can investigate, propose and build. REA shows the value of evidence in reverse engineering; those who call for caution warn against losing business knowledge; TODM proposes separating authority and acceptance; architectural patterns let us rebuild guarantees in different environments. The result is a discipline, not a magic tool.

There is a sentence that sums up my position: **a 1:1 modernization can be a bridge, but we should never mistake the bridge for the city we want to reach**. If after changing the language we keep deploying the same way, locking the same way, accumulating dependencies the same way and without knowing how to demonstrate what the system does, we have not modernized it. We have only changed the language of its problems.

## The contract, with its evidence

| Clause | Artifact that demonstrates it | Where it appears in the book |
|---|---|---|
| Identifiable evidence of what the system does | Inventory with hashes and EvidenceItems | Chapters [6](../part-2-archaeology-and-authority/06-rea-and-archaeology-that-leaves-a-trail.md) and [7](../part-2-archaeology-and-authority/07-legacy-archaeology-assisted-by-agents.md) |
| Invariants and exceptions in an approved baseline | Versioned baseline with a protected anchor | Chapters [10](../part-3-oracles/10-todm-and-the-problem-of-accepting-what-we-build.md) and [12](../part-3-oracles/12-cobol-and-c-must-agree-on-meaning.md) |
| Old responsibilities with a justified new mechanism | Substitution matrix and ADRs | Chapter [13](../part-4-patterns/13-before-choosing-a-pattern-identify-the-contract.md) and Annex [D](../annexes/annex-d-architecture-decisions.md) |
| Independent oracles, also for concurrency and failures | Qualified gate and accounting oracle | Chapters [17](../part-4-patterns/17-from-mainframe-locks-to-explicit-concurrency-control.md), [27](../part-6-lab/27-making-the-error-visible.md) and [28](../part-6-lab/28-transfers-locks-and-failures-locally.md) |
| Realistic load test with documented cost | Completed and approved performance contract | Chapters [22](../part-5-capacity/22-mips-do-not-fit-in-a-vcpu-conversion.md) to [25](../part-5-capacity/25-azure-or-a-huge-machine-at-the-customer-s-site.md) |
| Controlled transition of data, support and recovery | Ownership register and rehearsed return plan | Chapters [16](../part-4-patterns/16-data-ownership.md) and [30](30-from-the-lab-to-a-system-that-keeps-running.md) |
| Verified retirement of the legacy | Telemetry without residual dependencies | Chapters [14](../part-4-patterns/14-strangler-fig-change-the-edge-before-the-heart.md) and [33](33-modernization-plan-first-a-capability-test-then-a-bet.md) |

> **If after changing the language we keep deploying the same way, locking the same way and without knowing how to demonstrate what the system does, we have not modernized it. We have only changed the language of its problems.**

---

[← Chapter 36 · A hundred risks for choosing patterns with judgement](36-a-hundred-risks-for-choosing-patterns-with-judgement.md) · [Contents](../README.md) · [Epilogue →](../epilogue.md)
