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

## Three inspectable findings

1. **Recovered deadlock:** PostgreSQL returned `40P01`; the whole transaction was retried and both transfers ultimately committed without duplicate postings.
2. **Isolation matters:** the negative control left zero active operators under `READ COMMITTED`. With `SERIALIZABLE`, one stayed active and two `40001` failures were observed.
3. **An oracle that contradicts:** removing a posting made the independent read-only checker reject the ledger via `balancedPostings`, `projectionAgrees` and `twoPostingsPerCommit`.

**Offline evidence-integrity check:**

```bash
python3 scripts/check_e1_observations.py
```

The check verifies original source SHA-256 values and cited controls. Each JSON preserves `runId`, `jobId`, source commit, limitations and observations. The elapsed time reflects only **this synthetic test**, not production transactional latency.

The overall experiment remains **E1 partially verified**: E1c and comprehensive reference-contract parity are outstanding.
