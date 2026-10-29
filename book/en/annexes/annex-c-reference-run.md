**English** · [Español](../../es/anexos/anexo-c-ejecucion-de-referencia.md)

[← Annex B · Lab contract](annex-b-lab-contract.md) · [Contents](../README.md) · [Annex D · Architecture decisions →](annex-d-architecture-decisions.md)

# Annex C · Reference run

Local run verified on 29 October 2026. The .NET SDK used was 10.0.403 and the compiler cobc (GnuCOBOL) 3.1.2.0. The 58 cases completed the COBOL and C# comparison. The ten acceptance controls produced the expected verdicts.

| Control | Observed verdict | Observed delivery |
|---|---|---|
| none | PASS | SIMULATED_ALLOW |
| round-even | FAIL | BLOCK |
| wrong-threshold | FAIL | BLOCK |
| approve-inactive | FAIL | BLOCK |
| missing-evidence | INCONCLUSIVE | BLOCK |
| missing-case | INCONCLUSIVE | BLOCK |
| duplicate-case | INCONCLUSIVE | BLOCK |
| invalid-anchor | INCONCLUSIVE | BLOCK |
| no-mandate | PASS | BLOCK |
| equal-but-wrong | FAIL | BLOCK |

The transactional module ended with PASS. Its controls checked a race over a balance, duplicates, identity conflict, rollback, process crash, lost response after commit, lock wait, retry exhaustion and rejection of a deliberately corrupted history. The six reconciliation invariants were true.

The SQLite library used by the C# process was 3.45.1 and that of the Python verifier 3.53.1. The version difference is recorded so as not to attribute an identical environment to both processes.

The complete results and source hashes are in `reference-results/summary.json` and `reference-results/bank/summary.json`, which the lab keeps unmodified. The local measurements have no mainframe baseline and no Azure run. Their result cannot be used to approve enterprise capacity.

To repeat the process, follow Annex [A](annex-a-a-lab-that-can-prove-us-wrong.md): `bash scripts/run-podman.sh --auto` with Podman, or `python3 walkthrough.py --auto --bank` in the native environment described. A new run writes its own record in `results/`.

## Offline verification

`tools/verify_offline.py` checks what can be checked without compilers. Its result: the baseline anchor matches; a third implementation of the policy in Python reproduces the 58 expected results; every core source —`fee.cob`, `Candidate`, `Gate`, `Bank`, `run.py`, `bank_test.py` and `cases.json`— is byte-identical to the one recorded in the reference run; and the accounting oracle accepts the nine valid persisted databases and rejects the negative control because of unbalanced postings, operations without two postings and balances that cannot be rebuilt from the history. `walkthrough.py` and `cobol_local.py` differ from the reference run only in the text they display.

---

[← Annex B · Lab contract](annex-b-lab-contract.md) · [Contents](../README.md) · [Annex D · Architecture decisions →](annex-d-architecture-decisions.md)
