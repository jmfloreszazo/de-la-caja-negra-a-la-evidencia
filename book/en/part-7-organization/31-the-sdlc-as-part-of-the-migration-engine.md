**English** · [Español](../../es/parte-7-organizacion/31-el-sdlc-como-parte-del-motor-de-migracion.md)

[← Chapter 30 · From the lab to a system that keeps running](30-from-the-lab-to-a-system-that-keeps-running.md) · [Contents](../README.md) · [Chapter 32 · A migration story: the account that looked easy →](32-a-migration-story-the-account-that-looked-easy.md)

# Chapter 31 · The SDLC as part of the migration engine

> [!IMPORTANT]
> **Chapter thesis.** Good SDLC practices work in our favour when they turn uncertainties into repeatable checks. Switching them off just when AI lets us generate code faster than ever would be a mistake.

One of the ironies of modernizing COBOL is that the organization may today have a far richer engineering discipline than the one that existed when the system was written. It would be a mistake to switch off that advantage precisely because we want AI to generate code fast. The modern SDLC infrastructure lets us turn the speed of agents into repeatable evidence.

## Starting before having the whole system

Good SDLC practices work in our favour when they turn uncertainties into repeatable checks. An input contract lets us run the same case against two implementations. An ADR keeps why we chose an isolation level or a partition. A regression test prevents reintroducing a difference we had already resolved.

I would bring performance and recovery objectives in from discovery. Microsoft's Well-Architected framework recommends setting measurable criteria and testing continuously under representative conditions [28]. For TODM, that translates into capacity and recovery oracles as well as functional ones.

I would not set the project's targets by copying figures from the example. The service owner must establish the necessary work, the times, the states allowed during a failure and the budget. Those criteria need approval and a version, just like a fee rule.

## A chain of evidence during development

| Moment | Practice | Useful evidence for migration |
|---|---|---|
| Discovery | Inventory and characterization | What the system does and where we have doubts |
| Design | Transaction and concurrency ADRs | Which guarantees each boundary preserves |
| Build | Tests, analysis and review | Local defects and contract changes |
| Integration | Differential and history tests | Equivalence and concurrent conflicts |
| Performance | Load, stress and soak | Capacity under fixed conditions |
| Resilience | Failures and recovery | Committed state and time to restore |
| Delivery | Immutable artifacts and authorization | Exactly what was verified and delivered |
| Operations | Telemetry and reconciliation | Drift, queues and rules to review |

A quick test can run on every change. Long or expensive tests can run at milestones and on controlled infrastructure. The frequency must respond to the regression risk and the cost. Running a noisy load for thirty seconds on any runner does not produce a reliable capacity gate.

The repository must version sources and specifications, control permissions and separate proposal branches from approved baselines. Pipelines run parsing, linters, SAST, SBOM, characterization tests, contract tests, mutation, concurrency, load and artifact verification. Agents can open PRs and explain differences, but they must not be able to lower thresholds or edit the trusted verifier to get a green build. Signatures, hashes and change control are useful to reasonably attribute which artifacts were evaluated; they do not replace a verifiable human identity or business judgement.

Observability stops being an operations product and becomes part of the oracle. I would define correlated traces for a business transaction, latency and lock metrics, controlled cardinality, balance reconciliation, validation errors, CDC lag and outbox state. A modernization defect may not show up as an exception; it may be a statistical deviation in amounts, an increase in retries or a queue that does not finish before the bank opens.

## The evidence sheet of every pull request

Each PR should include an **evidence sheet**: proposed change, affected rules, fixtures added, oracle results, coverage, performance effects, dependencies and rollback criterion. Human review must focus on material differences and the integrity of the process, not on approving thousands of generated lines blindly.

This is the template I would put in the repository. The author of the change —person or agent— writes it, and the pipeline validates it, not good faith.

**Listing 31.1 · Evidence sheet template for a modernization PR** — *Illustrative*

```markdown
## Evidence sheet
- Capability: fee-calculation · Mandate: MND-2026-114
- Affected rules: R-FEE-003 (rounding), no baseline change
- Baseline: contracts/cases.json @ 976d7127… (anchor verified by CI, not by the author)
- Candidate: sha256 of the binary published by the build, not the local one
- Oracles: G5 functional PASS 58/58 · G3 controls 10/10 · bank invariants 6/6
- Performance: no change in the critical path / capacity trial not required
- Authorized divergences from the legacy: none
- Rollback: revert the PR; no data migration
- Open questions: behaviour with production compiler options (EV-0142)
```

![Figure 31.1 · The baseline lives on its own protected branch: the candidate is merged when it passes G5 and G6, and a rule change opens a G7 revision.](../../figures/en/gitgraph.png)

*Figure 31.1 · The baseline lives on its own protected branch: the candidate is merged when it passes G5 and G6, and a rule change opens a G7 revision.*

And this is the continuous integration that backs it. It is the template included in the lab; it is ready to copy to `.github/workflows/`, but it has not been enabled in any repository.

**Listing 31.2 · ci/github-actions.yml in the lab** — *Template · not enabled*

```yaml
name: COBOL and transactional evidence
on: [push, pull_request, workflow_dispatch]
permissions:
  contents: read
jobs:
  acceptance:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '10.0.x'
      - run: sudo apt-get update && sudo apt-get install -y gnucobol3 libsqlite3-0
      - run: python3 tools/verify_offline.py
      - run: python3 walkthrough.py --auto --bank
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: execution-evidence
          path: results/
```

![Figure 31.2 · The pipeline as the migration engine: every stage leaves evidence and authorization consumes the exact artifact.](../../figures/en/pipeline.png)

*Figure 31.2 · The pipeline as the migration engine: every stage leaves evidence and authorization consumes the exact artifact.*

Look at `permissions: contents: read` and `if: always()`. The first prevents the pipeline from modifying the repository it evaluates. The second keeps the evidence even when the gate blocks, which is precisely when it is needed most.

## Making optimization accountable

When we change an index, the batch size, the isolation level or the number of workers, the improvement must face two questions: how much it improves the metric and which guarantee it preserves. A latency drop achieved by disabling durable commit is not an equivalent optimization if the contract required that durability.

I would version the generator, the mix, the data, the configurations and the approval criteria. I would keep raw results, not just the final chart. The record must allow us to distinguish a code improvement from an infrastructure change or an already warm database.

Agents can prepare tests, summarize discrepancies and propose optimizations. The gate must use the observed evidence and keep the protected criterion out of the builder's write scope. Delivery authorization also includes the conditions under which capacity was measured.

> **Agents can open PRs and explain differences. They must not be able to lower the thresholds or edit the verifier to get a green build.**

---

[← Chapter 30 · From the lab to a system that keeps running](30-from-the-lab-to-a-system-that-keeps-running.md) · [Contents](../README.md) · [Chapter 32 · A migration story: the account that looked easy →](32-a-migration-story-the-account-that-looked-easy.md)
