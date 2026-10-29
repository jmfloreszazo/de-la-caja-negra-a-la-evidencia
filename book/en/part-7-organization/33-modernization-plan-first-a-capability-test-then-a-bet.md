**English** · [Español](../../es/parte-7-organizacion/33-plan-de-modernizacion-primero-una-prueba-de-capacidad.md)

[← Chapter 32 · A migration story: the account that looked easy](32-a-migration-story-the-account-that-looked-easy.md) · [Contents](../README.md) · [Chapter 34 · Measuring what we do not yet know →](34-measuring-what-we-do-not-yet-know.md)

# Chapter 33 · Modernization plan: first a capability test, then a bet

> [!IMPORTANT]
> **Chapter thesis.** Management does not need promises that AI will convert everything. It needs staged decisions, bounded investment and explicit criteria to stop.

Management does not need promises that "AI will convert everything". It needs staged decisions, bounded investment and criteria to stop. I would propose a **Discovery** that measures inventory, criticality, dependencies, data semantics and observable capacity. Then a **Pilot** with a seam selected for risk and relevance, not for how good it looks in a demo. Then a **Parallel Run** with functional, operational and performance oracles. Only then a gradual rollout and a controlled retirement of the previous component.

Each stage closes with three questions. What property have we demonstrated? What uncertainty remains open? What risk does the next stage take on? A pilot may conclude that keeping COBOL is better. It may also conclude that the migration is viable but requires changing the data model. An early negative result is valuable: it avoids committing millions to a wrong hypothesis.

Governance must prevent false progress. I would not count converted lines as business progress. I would measure capabilities freed from dependencies, rules covered, failures found, change lead time, cost per operation, debt retired and real risk reduction. For AI I would include the percentage of proposals accepted unchanged, defects detected by independent oracles, agent cost and specification drift. No single metric sums up a modernization.

There is also an organizational design obligation: COBOL specialists are not an obstacle to remove; they are part of the domain authority. Their knowledge must be transferred to the evidence contract and to the team that will operate the new system. The goal is not to replace people with agents. It is to stop the business depending indefinitely on tacit knowledge that cannot be audited.

It was the concern I heard most often at Microsoft Frontier Transformation Week, where I took part as an MVP and moderator: moving from pilots to results takes maturity, leadership, governance and identity, not more demos [47]. A COBOL modernization is an extreme case of that same gap, because the pilot can go well and month-end close can still fail.

## Four stages with an exit

| Stage | What it demonstrates | Exit evidence | It may conclude |
|---|---|---|---|
| Discovery | What exists, what it does and how much work it sustains | Inventory with hashes, workload footprint, transactional map | That it is not worth continuing |
| Pilot | That a relevant seam can be rebuilt and accepted | Approved baseline, qualified gate, PASS candidate | That the data model must change first |
| Parallel run | Functional, operational and capacity equivalence with real traffic | G5 reports, reconciliation, worst-day trial | That the chosen platform does not make it |
| Gradual rollout and retirement | That the legacy is no longer needed for that capability | Ownership transferred, telemetry without residual calls | That the capability is retired |

![Figure 33.1 · A plan with exits: each stage may conclude that we should not go on, and that is a result too.](../../figures/en/plan.png)

*Figure 33.1 · A plan with exits: each stage may conclude that we should not go on, and that is a result too.*

> **An early negative result is valuable: it avoids committing millions to a wrong hypothesis.**

---

[← Chapter 32 · A migration story: the account that looked easy](32-a-migration-story-the-account-that-looked-easy.md) · [Contents](../README.md) · [Chapter 34 · Measuring what we do not yet know →](34-measuring-what-we-do-not-yet-know.md)
