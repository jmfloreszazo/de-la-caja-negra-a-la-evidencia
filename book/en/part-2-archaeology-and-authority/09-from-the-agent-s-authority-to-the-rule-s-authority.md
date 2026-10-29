**English** · [Español](../../es/parte-2-arqueologia-y-autoridad/09-de-la-autoridad-del-agente-a-la-autoridad-de-la-regla.md)

[← Chapter 8 · The agent's knowledge and the system's record](08-the-agent-s-knowledge-and-the-system-s-record.md) · [Contents](../README.md) · [Part III · Oracles: the right to accept →](../part-3-oracles/README.md)

# Chapter 9 · From the agent's authority to the rule's authority

> [!IMPORTANT]
> **Chapter thesis.** Orchestrating decides what runs; governing decides who can accept a consequence. An implementation can be correct and not authorized, and vice versa.

## Orchestrating and governing answer different questions

An orchestrator decides which task runs next, who it is assigned to and how a failure is recovered. Governance establishes who can grant permissions, what scope they have and who can accept a consequence. Both functions can collaborate, but they are worth distinguishing.

In the Leviathan article I used political institutions as a tool for architectural reasoning [1]. I do not attribute citizenship or moral legitimacy to a software process. I am interested in a practical question: which limits remain when the actor exercising a capability changes.

A supervisor that writes requirements, modifies code, redefines tests and authorizes delivery concentrates every decision. Splitting those steps among four agents does not necessarily solve the problem. If they share permissions and can adjust the criteria to fit the result, the separation exists only in the diagram.

The independence we need has several dimensions. The source of the expected result must be able to challenge the implementation. The evaluator must run under known conditions. Permissions must prevent the builder from unilaterally changing the reference. Authorization must correspond to the artifact that was verified.

## A concrete mandate

"You are the agent responsible for modernization" is not a sufficient operational authorization. A useful mandate might allow modifying a candidates folder, running a set of tools in an isolated environment and spending a given budget over an interval. It might forbid modifying approved contracts and publishing results as production deliveries.

The restriction has to be enforced where the action runs. A message asking the agent to respect the mandate helps guide it; it does not replace write control or the check immediately before a critical call.

When an agent delegates, the new task must stay within the authority it received. If a builder cannot modify the baseline, its sub-agent should not gain that ability simply because it is called a reviewer. The name of a role grants no permissions.

Revocation also needs an effective path. An expired mandate should not keep working because someone still holds a credential. In production, this requirement affects the identity provider, the enforcement points and the check immediately before a sensitive operation.

A useful mandate can be written down. This example describes what the builder agent can do in the lab. It is not a control in itself: it is the description that the enforcement point —the file system, the repository, the runner, the identity provider— has to apply.

**Listing 9.1 · A bounded mandate for the builder agent** — *Illustrative*

```yaml
mandate:
  id: MND-2026-114
  scope: capability/fee-calculation
  grantedTo: agent/builder
  grantedBy: owner/payments-domain      # in production, a verifiable human identity
  validFrom: 2026-10-29T08:00:00Z
  validUntil: 2026-11-05T20:00:00Z
  allow:
    write: ["Candidate/**"]
    execute: ["dotnet build", "dotnet test", "python3 run.py"]
    budget: { tokens: 2000000, wallClockHours: 6 }
  deny:
    write: ["contracts/**", "Gate/**", "ci/**"]
    actions: ["publish", "approve-baseline", "delegate-beyond-scope"]
  revocation: "revoked at the identity provider; checked before every action"
```

The most important line is `deny.write`. If the builder can write to `contracts/` or `Gate/`, the rest of the mandate is literature.

![Figure 9.1 · The mandate is enforced at the enforcement point, not in the prompt.](../../figures/en/mandate_seq.png)

*Figure 9.1 · The mandate is enforced at the enforcement point, not in the prompt.*

## Correct is not the same as authorized

An implementation can pass the tests and still not be authorized for release. Perhaps the scope changed, the approval expired or someone intends to deploy a different binary. Conversely, a team can be authorized to work and produce a result that breaks the contract.

The lab keeps this separation. It includes a case where the behaviour verdict is PASS and delivery is blocked for lack of a mandate. The authorization is synthetic; there is no enterprise identity behind it. The example teaches the logic of the decision, not a real permissions integration.

Keeping both dimensions visible prevents the green of a test from becoming an implicit authorization for any subsequent action.

> **The name of a role grants no permissions.**

---

[← Chapter 8 · The agent's knowledge and the system's record](08-the-agent-s-knowledge-and-the-system-s-record.md) · [Contents](../README.md) · [Part III · Oracles: the right to accept →](../part-3-oracles/README.md)
