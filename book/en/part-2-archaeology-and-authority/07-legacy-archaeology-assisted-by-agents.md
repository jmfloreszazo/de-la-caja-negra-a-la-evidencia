**English** · [Español](../../es/parte-2-arqueologia-y-autoridad/07-legacy-archaeology-asistida-por-agentes.md)

[← Chapter 6 · REA and archaeology that leaves a trail](06-rea-and-archaeology-that-leaves-a-trail.md) · [Contents](../README.md) · [Chapter 8 · The agent's knowledge and the system's record →](08-the-agent-s-knowledge-and-the-system-s-record.md)

# Chapter 7 · Legacy Archaeology assisted by agents

> [!IMPORTANT]
> **Chapter thesis.** An AI-assisted migration starts better with questions than with generation prompts. Specialized agents receive typed inputs, produce verifiable artifacts and operate with limited permissions.

An AI-assisted migration starts better with questions than with generation prompts. Which programs modify this account? Where is the interest decided? How many dialects, versions and copybooks are there? What happens when the final write fails? What changes arrive through nightly jobs? Who maintains the code tables? Answering requires combining syntactic analysis, metadata and dynamic observation.

I propose a chain of specialized agents under a common controller: **inventory and provenance**, **parser and dependency graph**, **rule discovery**, **execution observer**, **specification writer**, **architecture designer**, **builder**, **verifier** and **drift auditor**. They are not nine chatbots giving opinions on the same file. Each receives typed inputs, produces verifiable artifacts and operates with limited permissions.

The COBOL analyser generates an AST of the real dialect, resolves copybooks and locates data references, CALLs, embedded SQL and control structures. I would not ask an LLM to replace the parser. The agent takes the result and produces hypotheses about intent: for example, "a withdrawal on blocked accounts returns a specific code without modifying state". That hypothesis must come with paths, positions, observed examples and limitations. If production execution cannot be observed, we document the risk and design tests on an authorized copy.

REA is a useful methodological reference for investigation with tools and evidence [35, 3]. For the mainframe, its concrete support must be evaluated before it is claimed; I would not confuse "inspired by REA" with "REA natively analyses CICS". The integration architecture could use a neutral contract such as `EvidenceItem`, with hashes, provenance, coverage and an `observed / inferred / unknown` status. That lets findings flow between analysers and agents without losing their origin.

## From archaeologist to agent

AI lowers the cost of following calls, grouping variables, drafting hypotheses and suggesting test scenarios. It can generate a knowledge graph and propose domain boundaries. But it must not have permission to erase uncertainties or approve its own hypotheses. The responsibility of an investigating agent ends where the authority of the specification begins. Separating the two will be decisive when the system processes real money.

## A chain with permissions, not a choir of chatbots

Each link in the chain has an input, an output artifact and something it is expressly not allowed to do. The last column is what separates a governable agent system from an enthusiastic conversation.

| Agent | Receives | Produces | Cannot |
|---|---|---|---|
| Inventory and provenance | Repositories, datasets, catalogs | Inventory with hashes and owners | Modify sources |
| Parser and graph | Sources with resolved copybooks | AST, graph of CALL, COPY and SQL | Infer business intent |
| Rule discovery | Graph and observed executions | Hypotheses with locators | Approve rules |
| Execution observer | Authorized environment | Input, state, output and effects | Run outside the mandate |
| Specification writer | Approved hypotheses | Specification, DMN, scenarios | Change the baseline |
| Architecture designer | Specification and constraints | ADRs and comparable options | Choose without capacity evidence |
| Builder | Public contract | Candidate and its own tests | Touch protected oracles |
| Verifier | Pinned candidate and baseline | PASS, FAIL or INCONCLUSIVE | Authorize delivery |
| Drift auditor | Production and current baseline | Review alerts | Rewrite criteria |

![Figure 7.1 · The agent chain: each link produces an artifact and none writes the baseline.](../../figures/en/agent_chain.png)

*Figure 7.1 · The agent chain: each link produces an artifact and none writes the baseline.*

## The living specification

The result of this archaeology is not a frozen PDF. It is a versioned set of intent, specification, architecture, rules, decisions and tests: `intent.md`, `spec.md`, `plan.md`, ADRs, Gherkin scenarios, DMN tables and evidence manifests. Each rule must be able to answer "where did it come from?" and "which test verifies it?". Each transformation must be able to answer "which approved rule is it trying to satisfy?".

Not all legacy code deserves to be converted. The analysis must identify dead paths, duplicates, expired functions and behaviours the business wants to retire. But the decision to remove them is a functional decision with impact, not a side effect of a generated refactoring.

> **The responsibility of an investigating agent ends where the authority of the specification begins.**

---

[← Chapter 6 · REA and archaeology that leaves a trail](06-rea-and-archaeology-that-leaves-a-trail.md) · [Contents](../README.md) · [Chapter 8 · The agent's knowledge and the system's record →](08-the-agent-s-knowledge-and-the-system-s-record.md)
