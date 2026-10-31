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

**Not yet demonstrated on the final PR HEAD:** GitHub-hosted CI execution, original immutable log/artifact, real static COBOL parser, runtime capture, complete batch/authorization contracts, business signoff or bilingual generated-book validation.

## Full manuscript regeneration gate

After changes to the book chapter indexes, run the repository generator from its root:

```bash
python3 scripts/build.py
python3 scripts/check.py
cd lab/decomposition && python3 -m unittest discover -v -p 'test_*.py'
```

Commit both regenerated `book/es.md` and `book/en.md` in the same draft PR **only after** verifying that the generated content exactly follows the indexed ES/EN source chapters. The current draft has the chapter source and both indexes but **the monolithic editions have not yet been regenerated**; the book consistency gate may therefore fail. Do not confuse a missing GitHub Actions run with a passing test. PDF builds are likewise unverified. Never edit generated whole-book Markdown by hand and never alter the published release.
