**English** · [Español](../../es/parte-2-arqueologia-y-autoridad/08-el-conocimiento-del-agente-y-el-expediente-del-sistema.md)

[← Chapter 7 · Legacy Archaeology assisted by agents](07-legacy-archaeology-assisted-by-agents.md) · [Contents](../README.md) · [Chapter 9 · From the agent's authority to the rule's authority →](09-from-the-agent-s-authority-to-the-rule-s-authority.md)

# Chapter 8 · The agent's knowledge and the system's record

> [!IMPORTANT]
> **Chapter thesis.** An agent's memory helps it work. The system's record allows acceptance. Important knowledge must outlive the model that summarized it and the session that discovered it.

## Remembering is not proving

An agent may keep a note saying a certain fee is rounded in a certain way. That note helps it keep working. However, whoever must accept the migration needs more: the exact rule, its provenance, the current approval and the executions that checked it.

In "From Leviathan to Autopilot" I propose separating agent memory from the institutional record [1]. Applied to modernization, it means important knowledge must outlive the model that summarized it and the session that discovered it. An agent disappearing should not erase the reason we accepted a change.

The record of a transformation gathers facts, decisions and results. It can start with versioned files. It does not require a sophisticated platform from day one. It does need clear relationships: this version of the rule was approved for this scope; this candidate was verified against it; these results belong to this run.

A hash helps check content identity. It does not prove the content is correct or that whoever approved it had the authority. If the same actor can replace both the file and the expected hash, both can remain consistent after an improper change. Protection requires an anchor outside their control.

There is an idea I already defended when auditing Copilot agents in VS Code: git is the only version that matters, and auditing is not the same as preventing [40]. Applied to modernization, it means the rule we accept, the prompt that produced it and the candidate that satisfies it must be reconstructible from a versioned repository, not from the memory of a session. And a perfect trace of what an agent did lets us explain an error, but not prevent it: that takes permissions enforced where the action happens.

In "Agent Host Protocol (AHP)" I reached a sister conclusion: the owner of the session state is the host, not the editor; clients are views [44]. The record of a modernization applies that idea one level up. The state that matters —the approved rule, the evidence, the decision— does not live in the tool we work with, but in a record that every tool consults and none owns.

## Hypotheses must be able to lose

A comprehension agent proposes an interpretation. If all subsequent information is organized to confirm it, we will have a coherent and perhaps false story. The record must keep questions that could refute it.

For a fee, I would look for values that distinguish truncation, round-half-to-even and rounding away from zero. For an authorization rule, I would test the exact threshold and the value immediately above it. For a transition, I would examine the prior state and the absence of events that should be mandatory.

These discriminating tests are more informative than repeating a hundred times a case where every interpretation produces the same result. Designing them requires understanding the semantic risk. Quantity of examples helps later; first we need to know which disagreement they could reveal.

We must also keep the possibility that evidence is missing. A timeout may mean the program failed, the infrastructure did not respond or our adapter did not collect the result. Turning every absence into an empty value and carrying on destroys that distinction.

## Changing models without losing the work

Continuity becomes easier when contracts do not depend on an agent's private conversation. We can replace the model in charge of building a candidate and keep the same approved rule set. We can improve an analysis tool and compare its findings with the previous ones.

The model's identity and configuration remain relevant for reproducing the process. But they should not become the source of legitimacy for the result. The acceptance criterion belongs to the project and its owners.

That design also makes human review easier. The expert does not need to read every generated token. They need to understand the decisions that change behaviour and the evidence meant to justify them. Their time is better spent when the system presents concrete discrepancies and well-bounded questions.

> **Remembering is not proving. A hash proves identity, not correctness.**

---

[← Chapter 7 · Legacy Archaeology assisted by agents](07-legacy-archaeology-assisted-by-agents.md) · [Contents](../README.md) · [Chapter 9 · From the agent's authority to the rule's authority →](09-from-the-agent-s-authority-to-the-rule-s-authority.md)
