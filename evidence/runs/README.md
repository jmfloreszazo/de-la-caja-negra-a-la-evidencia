# Executed evidence · E1 PostgreSQL and .NET 10

This is **experimental evidence**, not a benchmark or a claim of mainframe equivalence. The accompanying JSON files were extracted from the result blocks emitted by **real GitHub Actions runs**. They are neither reconstructed screenshots nor fabricated example results.

| Test | E1a · PostgreSQL/Python | E1b · PostgreSQL/.NET 10 |
|---|---|---|
| Provenance | [CI #40921291469](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40921291469) | [CI #40919773614](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614) |
| Versioned evidence | [e1a.json](e1a.json) | [e1b.json](e1b.json) |
| Verdict | PASS, 11 controls | PASS, 7 controls |
| Real contention | `40P01` observed and full transaction retried | Concurrent transfers; no claim of identical deadlock coverage |
| Isolation anomaly | `READ COMMITTED` breaks invariant; `SERIALIZABLE` raises `40001` and retries | Not covered in this subset |
| Ledger and outbox | Independent SQL oracle verifies conservation, postings and outbox | Persistent-state Python/C# comparison and external oracle |
| Negative control | Intentional removal of a posting detected | Independent oracle reused after C# cases |
| Tested environment | PostgreSQL 16.13, Linux/Podman runner | .NET 10, Npgsql 10.0.3 and PostgreSQL |
| Not demonstrated | Production load, MIPS, CICS, distributed recovery | All SQLite contract controls and SQL Server |

## Extended E1b observation · 30 October 2026

The original [7-control E1b record](e1b.json) remains unchanged. A **separate, actual GitHub Actions execution** added three controls to the .NET 10/Npgsql candidate: bounded `55P03` lock retry exhaustion (six attempts with no ledger side effects), successful retry and idempotency after unlocking, and an independent SQL oracle rejecting a deliberately corrupted .NET posting before the posting was restored.

[Immutable extended record](e1b-extended.json) · [GitHub Actions run #41024101879](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879) · [original job and raw artifact](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879).

**Observed: PASS for all 10 controls.** The original 7-control execution is historical and its source digest is pinned to its 2026-10-29 commit; the extended record's source digests are matched to the current branch. The offline validator does **not** pretend that the historical test script equals the updated one. Neither result completes the full SQLite reference contract, E1c, or E1 overall.

## Direct SQLite ↔ PostgreSQL contract parity · 30 October 2026

The new [immutable E1b-reference-parity JSON](e1b-reference-parity.json) preserves the **actual** [CI run #41031578923](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41031578923), its job and artifact identifiers, source commit, original checkout, source hashes, 16 individual cases and tool versions. The original **unchanged .NET 10/SQLite executable** and the **.NET 10/Npgsql PostgreSQL executable** received identical synthetic operations. After **each** case, balances, operation records, postings and outbox matched, with a passing independent PostgreSQL accounting oracle.

Coverage includes committed/rejected and duplicate operations, conflicting IDs, invalid inputs, exceptions and process death before commit, lost acknowledgment after commit and subsequent safe replay. A real SQLite write lock and a PostgreSQL row lock were each released while their respective clients retried; PostgreSQL observed `55P03` and then committed once. The six control groups and all 16 sequential cases passed.

**Not demonstrated:** the entire SQLite multiprocess workload matrix, identical lock implementations or timings, SQL Server equivalence, durability after power loss, WAN, or mainframe throughput. The earlier E1b records remain intact. E1 remains partially verified.

## Three inspectable findings

1. **Recovered deadlock:** PostgreSQL returned `40P01`; the whole transaction was retried and both transfers ultimately committed without duplicate postings.
2. **Isolation matters:** the negative control left zero active operators under `READ COMMITTED`. With `SERIALIZABLE`, one stayed active and two `40001` failures were observed.
3. **An oracle that contradicts:** removing a posting made the independent read-only checker reject the ledger via `balancedPostings`, `projectionAgrees` and `twoPostingsPerCommit`.

**Offline evidence-integrity check:**

```bash
python3 scripts/check_e1_observations.py
```

The checker validates recorded controls, current source SHA-256 values for current-code observations, and the pinned commit/source manifest of the historical E1b observation; it does not byte-match historical sources against updated code. Each JSON preserves `runId`, `jobId`, source commit, limitations and observations. The elapsed time reflects only **this synthetic test**, not production transactional latency.

The overall experiment remains **E1 partially verified**: E1c and comprehensive reference-contract parity are outstanding.
