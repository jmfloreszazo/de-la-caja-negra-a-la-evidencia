**English** · [Español](../../es/parte-2-arqueologia-y-autoridad/06-rea-y-la-arqueologia-que-deja-rastro.md)

[← Part II · Archaeology, knowledge and authority](README.md) · [Contents](../README.md) · [Chapter 7 · Legacy Archaeology assisted by agents →](07-legacy-archaeology-assisted-by-agents.md)

# Chapter 6 · REA and archaeology that leaves a trail

> [!IMPORTANT]
> **Chapter thesis.** Tools investigate, agents propose and evidence supports the claims. REA brings a discipline —provenance, coverage and explicit unknowns— that is worth more for COBOL than any promise of translation.

Lost documentation and accumulated rules are real problems. But an engineering clarification is worth adding: source code is not the only evidence. There are shared copybooks, dataset definitions, version control, historical deployments, JCL, CICS configurations, DDL, catalogs, load statistics, incidents, tickets and, above all, behaviours the system still executes. Some rules live in a parameter table. Others live in a routine nobody has called for years. Some are historical bugs that consuming systems depend on.

That is why I would not start by asking "convert these two million lines for me". I would start with an **evidence map**. Each artifact gets an identity, version, hash, origin, owner and constraints. A specific parser builds dependencies between programs and copybooks; JCL analysers reconstruct batch chains; an SQL extractor locates tables and transactions; an observation system captures inputs, outputs and execution effects. Agents correlate that information, but they do not automatically turn it into truth.

## What Reverse Engineer Anything brings

REA connects agents to software investigation tools through MCP and a command-line interface. Its documentation describes the analysis of native binaries, .NET assemblies, JavaScript applications and other targets, with evidence and limitations attached to results. Deep native analysis depends on providers such as Ghidra, Hopper or IDA [3].

I place it in the discovery phase. An agent can walk through findings, ask questions and relate results from different tools. That helps investigation. It does not automatically turn a reconstruction into an equivalent implementation, nor does it prove specialized support for every COBOL dialect, copybook, JCL or transactional environment.

The documentation I reviewed does not allow me to present REA as a native COBOL-to-.NET translator. For a COBOL system with sources, I would start with tools that understand those sources and their dialect. For a binary without sources, the path changes and requires different analysis capabilities.

This difference matters because "reverse engineering" groups very different problems. Recovering relationships between variables from source is not the same as reconstructing them from machine instructions. An assembly with metadata does not pose the same problem as a native executable either. The tool must be chosen according to the artifact available.

## What I learned from the VB6 case

Before writing this book I had to look closely at REA for a very practical reason: VB6 applications without sources that are still in production [35]. I downloaded the repository, read the code and checked the cases cited as proof. Three lessons from that work carry over almost literally to COBOL.

The first is that the interesting part is not the list of formats but **the output contract**. Every result is tied to evidence: path, size and SHA-256 of the artifact, the provider that produced it, the coverage and, above all, what it does not know. The states `unknown`, `partial`, `unsupported` or `truncated` are never aggregated as a success. It is a tool designed so the model does not fill gaps with imagination.

The second is its ledger of reconstruction obligations. A claim such as "this part is reconstructed" is only closed if it has an owner, test cases, a verifier that passes and a verifier authority comparable to that of the original observation. If any of the four is missing, the obligation stays open. That is exactly the discipline a business rule recovered from a COBOL program needs.

The third is that the hard knowledge usually already lives in specialized tools. In VB6, the project format and the P-Code are handled by tools with twenty years of history; the agent's contribution is driving them, crossing results and verifying. In COBOL the same happens with dialect parsers, JCL analysers and Db2 catalogs. **What was missing was not another parser: it was an agent able to use the existing ones with evidence discipline.**

But COBOL is not VB6. On a mainframe we usually have sources, copybooks and metadata; the problem is rarely decompiling and almost always reconstructing the semantics of a system spread across programs, data and operations. That is why I do not carry the *VBDec + REA + Ghidra* chain over as is. I carry over its principle.

## Three complementary approaches

ProLeap offers a COBOL parser based on ANTLR that builds a syntax tree and a semantic graph. Its documentation states that it extracts EXEC SQL, SQLIMS and CICS blocks as text [4]. It is a possible basis for structural analysis; I would not take it as a guarantee of execution or equivalence for all those extensions.

IBM documents a COBOL–Java validation path based on input and output recordings, resource mapping, and the generation and execution of JUnit tests [6]. It is a relevant reference for the capture-and-compare pattern, even though the documented target is Java and its integration is not that of this book's .NET lab.

AWS Transform documents code analysis, logic extraction and requirements generation for mainframe modernization, including extraction results and per-file issues [7]. This shows another approach focused on recovering structure and meaning. A vendor's documentation describes capabilities; an evaluation in our environment must check its real coverage.

These approaches do not necessarily compete in the same layer. REA can help investigate a binary, a parser can analyse sources and a modernization platform can organize a specific path. TODM proposes how to govern the acceptance of the result of that work. The concrete integration remains an engineering decision.

## A COBOL evidence adapter

I propose a component I call the COBOL Evidence Adapter. It is not a capability I attribute to REA, nor an integration already implemented in this lab. It is an architectural boundary: it receives artifacts and observations from the COBOL environment and presents them through a common contract.

Each finding should identify the artifact, its hash, the source locator, the tool and its version, the method used and the known limits. A relationship inferred by the agent would be recorded as a hypothesis. An observed execution would keep input, relevant state, output and conditions. An approved rule would have a different authority and version.

Imagine a fee rule found in a COBOL paragraph. The parser locates the expression. An execution confirms a result at the rounding boundary. The business owner confirms that this is the policy to be kept. They are three related pieces, but none replaces the others.

A knowledge graph can make navigating between them easier. Its value is not in using a graph database on principle, but in letting us reconstruct the path from a conclusion back to the evidence that supports it. A well-designed table may be enough to begin with.

Every finding should record: "claim", "source", "lines or transaction", "tool", "hash", "degree of certainty", "dynamic observation" and "open question". If a bonus rule is inferred from three examples, it must be flagged as a hypothesis. It will not become an approved baseline until a business authority or sufficient evidence supports it. The discipline of saying "we don't know" is an architectural capability.

This is how a finding from the lab would look expressed with that contract. The hash is the real one of the lab source; the format is a proposal.

**Listing 6.1 · An EvidenceItem: the claim, its provenance and what we still do not know** — *Illustrative*

```json
{
  "id": "EV-0142",
  "claim": "Active customer: the fee rounds to the cent; ties go away from zero",
  "status": "observed",
  "artifact": {
    "path": "legacy/fee.cob",
    "sha256": "136cc8c21ae514634f93b7139fb9e185b115e6b817c20890ad0e1f9265971cbf",
    "locator": "COMPUTE fee-cents ROUNDED"
  },
  "tool": { "name": "cobc", "version": "GnuCOBOL 3.1.2.0",
            "method": "execution with a fixed input" },
  "observation": { "input": "0000002500200Y", "output": "APPROVE|00000001" },
  "coverage": "one exact tie; no negatives or other compiler options",
  "unknowns": ["behaviour on Enterprise COBOL with production options"],
  "approval": null,
  "verifiedBy": []
}
```

Look at the last two fields. `approval` is empty because observing a behaviour does not turn it into approved policy. `verifiedBy` is empty because no candidate has yet shown it reproduces it. They are three related pieces, and none replaces the others.

![Figure 6.1 · Life cycle of an EvidenceItem: observing is not approving, and approving is not verifying.](../../figures/en/evidence_states.png)

*Figure 6.1 · Life cycle of an EvidenceItem: observing is not approving, and approving is not verifying.*

> **A demo shows a possibility. Evidence shows a property.**

---

[← Part II · Archaeology, knowledge and authority](README.md) · [Contents](../README.md) · [Chapter 7 · Legacy Archaeology assisted by agents →](07-legacy-archaeology-assisted-by-agents.md)
