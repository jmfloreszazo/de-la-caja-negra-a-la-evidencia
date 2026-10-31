# Synthetic mainframe decomposition oracle (research candidate)

This English-only Python 3 laboratory tests **design boundaries**, NOT production COBOL execution, bank consistency, a deployed migration, or real mainframe throughput.

```bash
cd lab/decomposition
python3 -m unittest discover -v -p 'test_*.py'
python3 oracle.py fixture.json
```

The fixture intentionally contains both a safe **candidate** read-model extraction and an unsafe ledger-only extraction. The CLI returns exit code **1** if any proposed cut is rejected, **2** for invalid evidence, and **0** only if all proposals are candidates. A candidate is **never** an approved migration.

Each graph edge has a provenance class, observation marker, confidence level and optional atomic transaction group. A cut through an atomic-group hyperedge, an unknown crossing dependency, or an inferred crossing dependency fails closed. Conflicting evidence attached to extracted nodes also rejects a proposed cut; the evidence-merge module does not discard original observations. The source graph is synthetic; no runtime trace has been gathered. The model is intentionally conservative and incomplete: an edge without an atomic label is **not** proof that the linked resources are independently safe. Before applying to a real estate, require business-owner sign-off, trustworthy domain/runtime evidence, atomic hyperedge validation, security/authorization invariants, timing/batch considerations, and real independent Oracle Gates.

Links: [English research](../../docs/research/mainframe-decomposition.en.md) · [Spanish research](../../docs/research/mainframe-decomposition.es.md) · issue #32. Published v2026.10.29 unchanged.

## Reproducible checks and evidence status

Run the entire offline suite above from this directory. The suite includes the base oracle, observation merge, pipeline integration and adversarial hyperedge controls. A green offline run only checks the synthetic model, **not** any deployed mainframe or the correctness of its discovered dependencies. Preserve stdout, source commit SHA, Python version and failed runs before describing this as a CI-verified result. The fixture contains an intentionally rejected proposal; `python3 oracle.py fixture.json` therefore returns **1 by design** and is not the test-suite exit code.

**Original #50 evidence:** 29 synthetic boundary tests, bilingual whole-book generation and PDF preview passed on GitHub Actions (source SHA `c48c269cd3b3d590b5791c31a89f2d463bcb5839`). Real bank behavior, authorized business observations, business signoff and mainframe-scale measurements remain unverified. Any later branch needs its own final-head checks.

## Full manuscript regeneration gate

After changes to the book chapter indexes, run the repository generator from its root:

```bash
python3 scripts/build.py
python3 scripts/check.py
cd lab/decomposition && python3 -m unittest discover -v -p 'test_*.py'
```

Commit both regenerated `book/es.md` and `book/en.md` in the same draft PR **only after** verifying that the generated content exactly follows the indexed ES/EN source chapters. The paired whole-book editions were regenerated and checked in PR #50. **New changes on subsequent branches must pass their own exact-head CI.** Do not equate missing or pending GitHub Actions runs with passing tests. Never edit generated whole-book Markdown by hand and never alter the published release.

## Functional-first greenfield rewrite (issue #32)

**No source parser is planned in this track.** Start with [30 hypothesized banking business capabilities](functional_capabilities.json), not COBOL programs, copybooks, tables or JCL step counts. The catalog is illustrative, **not evidence of any real bank's implemented features**.

Run the catalog quality checker:

```bash
cd lab/decomposition
python3 -m unittest discover -v -p 'test_*.py'
python3 functional_contract_gate.py functional_capabilities.json
```

The second command intentionally exits **1** and reports 30 `NEEDS_EVIDENCE` records because **none has authorized business evidence or an accountable reviewer**. That is the required fail-closed behavior, not a parser error or a failed unittest. Exit **2** denotes malformed data. Even an evidence-complete record is `READY_FOR_INDEPENDENT_REVIEW`, never automatically approved.

Find the bilingual method and worked contracts in [ES](../../docs/research/mainframe-functional-rewrite.es.md) and [EN](../../docs/research/mainframe-functional-rewrite.en.md). Required real inputs are business process owners, approved policies, observable external outcomes, failure cases, cut-off calendars, data/control lineage, SLA measurements and independent banking oracles. Preserve source references and permissions; do **not** commit live customer/financial records.
