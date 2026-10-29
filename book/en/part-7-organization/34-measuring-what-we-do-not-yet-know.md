**English** · [Español](../../es/parte-7-organizacion/34-medir-lo-que-todavia-no-sabemos.md)

[← Chapter 33 · Modernization plan: first a capability test, then a bet](33-modernization-plan-first-a-capability-test-then-a-bet.md) · [Contents](../README.md) · [Chapter 35 · When I would NOT migrate →](35-when-i-would-not-migrate.md)

# Chapter 34 · Measuring what we do not yet know

> [!IMPORTANT]
> **Chapter thesis.** The lab shows a mechanism; it does not show that TODM reduces defects compared with other ways of working. That question requires a protocol, an honest unit of analysis and the willingness to accept negative results.

## A reproducible result is not a comparative study

The lab shows a mechanism. It does not establish that TODM reduces defects compared with any other way of working. Nor does it establish the hours that bringing agents into a modernization would save.

The public TODM protocol distinguishes three conditions for studying construction with agents: tests coupled to the implementation, an independent oracle, and an independent oracle with mutation qualification. It proposes keeping tasks and budgets comparable, recording costs and analysing at task level [12]. That separation lets us ask questions a demo cannot answer on its own.

Does the independent oracle reduce accepted defects? What does its qualification add? How many incorrect blocks does it produce? How much effort does clarifying and approving rules require? Which attempts to modify the evaluator do real permissions prevent? Those questions need data and a prior design.

The TODM repository itself frames this as an open challenge: it invites anyone to reproduce, falsify, compare or transfer the method, and accepts negative or inconclusive findings as contributions [2]. A book that argues for evidence needs that door open.

## The unit of analysis matters

If we run the same task several times, we have repetitions of that task. If we inject ten mutations into one program, we have ten related variants. We should not present them as independent projects to artificially increase the sample.

Results must keep the grouping: task, variant, tool, model, run and condition. They must also include failed runs and those that remained inconclusive. Excluding them because they spoil the comparison changes the question we are answering.

The stopping rule is fixed before observing results when we aim for a confirmatory inference. A small pilot may be enough to find protocol failures or show feasibility. Learning from it does not automatically make it generalizable evidence of superiority.

## What building trust costs

I would measure the human time spent preparing data, clarifying rules, reviewing contracts and resolving discrepancies. I would add model consumption, tool execution, retries and the cost of maintaining the tests.

I would also measure what changes after delivery: escaped defects, diagnosis time, recovery and ease of changing a rule. If an investment in oracles reduces the time to reconstruct why a version was accepted, that benefit deserves to be observed. It must be measured, not assumed.

The architecture is not exempt from evaluation either. A permissions system can be well described and badly configured. We need to attempt unauthorized changes and observe that the environment prevents them. An agent's refusal in natural language does not prove it lacks the permission.

## A conclusion that may change

I am interested in a methodology capable of receiving negative results. If an oracle turns out too expensive for the risk it covers, it will have to be simplified. If a representation confuses business reviewers, it will have to change. If an agent barely improves on a deterministic workflow, perhaps we do not need that agent.

The value of the book does not depend on every hypothesis coming out in TODM's favour. It depends on the reader being able to distinguish a proposal from an observation and an observation from a sufficiently supported conclusion.

> **The value of the book does not depend on every hypothesis coming out in TODM's favour.**

---

[← Chapter 33 · Modernization plan: first a capability test, then a bet](33-modernization-plan-first-a-capability-test-then-a-bet.md) · [Contents](../README.md) · [Chapter 35 · When I would NOT migrate →](35-when-i-would-not-migrate.md)
