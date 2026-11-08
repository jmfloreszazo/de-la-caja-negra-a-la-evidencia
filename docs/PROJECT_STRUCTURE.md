# Project structure and contribution routes

This project has one bilingual book and several executable evidence laboratories.
Keep narrative, executable specifications, observed evidence and generated output
separate. Author and editorial authority: José María Flores Zazo · jmfloreszazo.com.

## Where a change belongs

| Location | Responsibility | Change rule |
|---|---|---|
| `book/es/`, `book/en/` | Paired source chapters, part indexes and annexes | Edit both editions; their root indexes define reading order |
| `book/es.md`, `book/en.md` | Generated single-page editions | Regenerate with `scripts/build.py`; never edit by hand |
| `book/figures/` | Paired diagram sources, rendered images and provenance | Keep source/theme/render lineage; do not substitute fabricated screenshots |
| `lab/` | English-only executable examples, bounded models, tests and independent oracles | Document commands and limitations in each lab README |
| `lab/decision_models/` | Limited decision/process profiles and ADR/baseline traceability | Explicit semantics and negative cases; not full OMG engines |
| `lab/todm_validation/` | Digest-bound evidence adapter and qualification | Technical verdict and authority remain separate |
| `scripts/azure/`, `infra/experiments/` | Azure operator, capture utilities and Bicep | Use explicit subscriptions and isolated resources; retain failures |
| `evidence/runs/` | Versioned observations, provenance and selected CLI captures | Add new observations; do not rewrite earlier runs to fit new claims |
| `lab/results/` | Ignored full raw campaigns, snapshots and runtime logs | Preserve campaign identity; do not treat temporary outputs as approved baselines |
| `docs/` | Engineering protocols, decisions and historical closeouts | Link current entry points; historical records describe their original date |
| `dist/` | Current generated PDFs and layout metadata only | Rebuild from sources; never store historical evidence here |
| `evidence/archives/` | Preserved delivery/evidence bundles and relocation inventory | Payloads under `preserved-dist/` stay ignored; preserve bytes, receipts and internal paths |

## Reading and execution paths

- Start with the [Spanish book](../book/es/README.md) or [English book](../book/en/README.md).
- Chapter 10 explains TODM; chapter 10 bis documents tools, models and ADR practice.
- Chapter 25 bis explains actual Azure observations and control-plane CLI captures.
- Chapter 29 distinguishes model inference, candidate execution and independent evaluation.
- Annex D records architecture decisions; final Annex H explains transfer to other languages.
- Start execution at the [lab guide](../lab/README.md), [experiment protocol](../lab/docs/EXPERIMENT_PROTOCOL.md)
  and [Azure runbook](../infra/experiments/README.md), not at a historical report.
- Consult the [execution roadmap](EXPERIMENT_ROADMAP.md) for current bounded results and open claims.

## Models, decisions and evidence are different

A proposed rule or diagram does not become authoritative because it validates.
The accountable baseline must bind exact version, semantics, scope and approval.
An ADR records why an option was selected; it links to rules and verification
obligations but does not replace them. Golden Master observations characterize
legacy behaviour without automatically approving it.

Model-source changes belong with their schemas, evaluator versions and tests.
Generated candidates and their test results belong to a named campaign. A new
experiment cannot overwrite protected reference snapshots or promote
`evidence/claims.json` without approved change control.

## Validate the structure

```bash
python3 scripts/build.py
python3 scripts/check_language_policy.py
python3 scripts/check.py
```

The checks cover relative links, paired structure and code fences, ordered book
coverage, regenerated editions, diagram provenance and method guardrails. Run
the relevant lab tests separately after executable changes. Build PDFs using
the [documented PDF workflow](PDF.md), and inspect modified chapters after rendering.

Keep releases, version changes, merges and GitHub workflow execution under the
author's explicit control. Local verification does not authorize publication.
