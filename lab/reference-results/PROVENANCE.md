# Provenance of the reference results

These files were produced by the native Linux execution of `run.py` and `bank_test.py` on 29 October 2026 and are kept **unchanged**.

* .NET SDK 10.0.403 · `cobc (GnuCOBOL) 3.1.2.0` · Linux 6.18 x86_64, glibc 2.39
* SQLite 3.45.1 in the .NET process, 3.53.1 in the Python verifier
* `summary.json` and `bank/summary.json` record the SHA-256 of every source that took part

At packaging time, `tools/verify_offline.py` confirmed that all core sources are byte-identical to the hashed ones. `walkthrough.py` and `cobol_local.py` were translated to English afterwards; only their user-facing strings changed.

`bank/negative-control.db` is corrupted on purpose: one posting was deleted so the accounting oracle must reject it. The `load-*.db` files come from small closed-loop local observations and are not capacity evidence.

A new run writes to `results/`, never here.
