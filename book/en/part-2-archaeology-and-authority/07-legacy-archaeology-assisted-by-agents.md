**English** · [Español](../../es/parte-2-arqueologia-y-autoridad/07-legacy-archaeology-asistida-por-agentes.md)

[← Chapter 6 · REA and archaeology that leaves a trail](06-rea-and-archaeology-that-leaves-a-trail.md) · [Contents](../README.md) · [Chapter 8 · The agent's knowledge and the system's record →](08-the-agent-s-knowledge-and-the-system-s-record.md)

# Chapter 7 · Legacy Archaeology assisted by agents

> [!IMPORTANT]
> **Chapter thesis.** AI-assisted modernization should start by asking **which business capabilities are needed and which guarantees must survive**. Who authorizes transfers? What happens when a reply is lost? Which exceptions and end-of-day rules apply? Interviews, approved policies, external contracts and authorized black-box tests establish the capability map first. Syntactic analysis may resolve later technical questions, but is neither mandatory nor a way to derive the new domain boundaries.

Start with the business capabilities and observable outcomes that have to survive a brownfield migration. Which customer journey authorizes a transfer, who owns account state, and which failures leave the result uncertain? Authorized interviews, policy, interfaces and black-box observations come first. Source and metadata inspection are optional ways to resolve named technical uncertainties, never the migration unit.

I propose specialized agents under one controller: **functional discovery and provenance**, **optional technical investigation**, **rule discovery**, **execution observer**, **specification writer**, **architecture designer**, **builder**, **verifier** and **drift auditor**. These are not nine chatbots giving opinions on the same file. Business authority defines the capabilities; the incumbent offers observations and sometimes technical clues. Each agent has typed inputs, artifacts and limited permissions.

Functional discovery first produces positive and negative scenarios, decisions and accountable owners. For example: "a withdrawal on blocked accounts returns a particular code without changing state". The hypothesis needs approved policy and corroborating observations. **If an unresolved question calls for legacy source inspection**, a COBOL dialect parser may examine AST, CALL, COPY or SQL; that branch is optional and does not dictate the target architecture. Unknowns remain open rather than being approved by an agent.

REA is a useful methodological reference for investigation with tools and evidence [35, 3]. For the mainframe, its concrete support must be evaluated before it is claimed; I would not confuse "inspired by REA" with "REA natively analyses CICS". The integration architecture could use a neutral contract such as `EvidenceItem`, with hashes, provenance, coverage and an `observed / inferred / unknown` status. That lets findings flow between analysers and agents without losing their origin.

## From archaeologist to agent

AI lowers the cost of following calls, grouping variables, drafting hypotheses and suggesting test scenarios. It can generate a knowledge graph and propose domain boundaries. But it must not have permission to erase uncertainties or approve its own hypotheses. The responsibility of an investigating agent ends where the authority of the specification begins. Separating the two will be decisive when the system processes real money.

## A chain with permissions, not a choir of chatbots

Each link in the chain has an input, an output artifact and something it is expressly not allowed to do. The last column is what separates a governable agent system from an enthusiastic conversation.

| Agent | Receives | Produces | Cannot |
|---|---|---|---|
| Functional discovery and provenance | Owners, policy, channels and authorized observations | Capabilities and uncertainties with sources | Approve rules |
| Optional technical investigation | Authorized source, copybooks and relevant metadata | Dependencies with coverage and provenance | Choose business boundaries |
| Rule discovery | Capabilities and observed outcomes | Hypotheses and exceptions with sources | Approve rules |
| Execution observer | Authorized environment | Input, state, output and effects | Run outside the mandate |
| Specification writer | Approved hypotheses | Specification, DMN, scenarios | Change the baseline |
| Architecture designer | Specification and constraints | ADRs and comparable options | Choose without capacity evidence |
| Builder | Public contract | Candidate and its own tests | Touch protected oracles |
| Verifier | Pinned candidate and baseline | PASS, FAIL or INCONCLUSIVE | Authorize delivery |
| Drift auditor | Production and current baseline | Review alerts | Rewrite criteria |

![Figure 7.1 · The agent chain: each link produces an artifact and none writes the baseline.](../../figures/en/agent_chain.png)

*Figure 7.1 · Brownfield modernization: business capabilities and contracts, independent TODM oracles, coexistence and G6 human authorization. Golden Master keeps legacy observations separate; COBOL/JCL investigation is optional. No agent modifies the approved baseline.*

## The living specification

The result of this archaeology is not a frozen PDF. It is a versioned set of intent, specification, architecture, rules, decisions and tests: `intent.md`, `spec.md`, `plan.md`, ADRs, Gherkin scenarios, DMN tables and evidence manifests. Each rule must be able to answer "where did it come from?" and "which test verifies it?". Each transformation must be able to answer "which approved rule is it trying to satisfy?".

Not all legacy code deserves to be converted. The analysis must identify dead paths, duplicates, expired functions and behaviours the business wants to retire. But the decision to remove them is a functional decision with impact, not a side effect of a generated refactoring.

> **The responsibility of an investigating agent ends where the authority of the specification begins.**

---

[← Chapter 6 · REA and archaeology that leaves a trail](06-rea-and-archaeology-that-leaves-a-trail.md) · [Contents](../README.md) · [Chapter 8 · The agent's knowledge and the system's record →](08-the-agent-s-knowledge-and-the-system-s-record.md)
