# Synthetic mainframe decomposition oracle (research candidate)

This English-only Python 3 laboratory tests **design boundaries**, NOT production COBOL execution, bank consistency, a deployed migration, or real mainframe throughput.

```bash
cd lab/decomposition
python3 -m unittest -v test_oracle.py
python3 oracle.py fixture.json
```

The fixture intentionally contains both a safe **candidate** read-model extraction and an unsafe ledger-only extraction. The CLI returns exit code **1** if any proposed cut is rejected, **2** for invalid evidence, and **0** only if all proposals are candidates. A candidate is **never** an approved migration.

Each graph edge has a provenance class, observation marker, confidence level and optional atomic transaction group. A cut across an atomic edge or an unknown-evidence edge fails closed. The source graph is synthetic; no runtime trace has been gathered. The model is intentionally conservative and incomplete: an edge without an atomic label is **not** proof that the linked resources are independently safe. Before applying to a real estate, require business-owner sign-off, trustworthy domain/runtime evidence, atomic hyperedge validation, security/authorization invariants, timing/batch considerations, and real independent Oracle Gates.

Links: [English research](../../docs/research/mainframe-decomposition.en.md) · [Spanish research](../../docs/research/mainframe-decomposition.es.md) · issue #32. Published v2026.10.29 unchanged.
