#!/usr/bin/env python3
"""Compare SQLite reference worker cases against the .NET/Npgsql candidate.

Replays the reference's exact logical commands for 1/2/4/8 workers, 32
operations per worker, uniform and hot-account traffic. SQLite runs its
original worker CLI processes. PostgreSQL uses concurrent Python workers
that invoke the same compiled .NET transfer CLI per operation. The client
process-launch models DIFFER, so no throughput/latency comparison is valid.
The E1 PostgreSQL database and SQLite file are disposable and reset per case.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time

from ledger import connect
from oracle import verify
from test_reference_parity import (
    DOTNET, HERE, LAB, OUT, SQLITE_DB, SQLITE_DLL, POSTGRES_DLL,
    initialize, original_snapshot, candidate_snapshot
)

WORKER_COUNTS = (1, 2, 4, 8)
OPERATIONS_PER_WORKER = 32
PATTERNS = ("uniform", "hot")


def sqlite_worker(worker, count, pattern, prefix):
    result = subprocess.run(
        [DOTNET, str(SQLITE_DLL), "worker", str(SQLITE_DB), str(worker),
         str(count), pattern, prefix],
        capture_output=True, text=True, timeout=120, env=os.environ
    )
    assert result.returncode == 0, (
        "SQLite worker", worker, result.returncode,
        result.stdout, result.stderr
    )
    rows = json.loads(result.stdout)
    assert len(rows) == count
    return rows


def postgres_worker(worker, count, pattern, prefix):
    results = []
    for i in range(count):
        src = 1 if pattern == "hot" else 1 + (worker*count+i) % 16
        dst = 2 if pattern == "hot" else 1 + src % 16
        operation = f"{prefix}-{worker}-{i}"
        proc = subprocess.run(
            [DOTNET, str(POSTGRES_DLL), "transfer",
             operation, str(src), str(dst), "1"],
            capture_output=True, text=True, timeout=40, env=os.environ
        )
        assert proc.returncode == 0, (
            "PostgreSQL command", operation, proc.returncode,
            proc.stdout, proc.stderr
        )
        result = json.loads(proc.stdout)
        assert result["status"] == "COMMITTED", (operation, result)
        results.append(result)
    return results


def execute_case(pattern, workers):
    initialize()
    prefix = "load"
    with ThreadPoolExecutor(max_workers=workers) as pool:
        sqlite_results = list(pool.map(
            lambda worker: sqlite_worker(
                worker, OPERATIONS_PER_WORKER, pattern, prefix
            ),
            range(workers)
        ))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        postgres_results = list(pool.map(
            lambda worker: postgres_worker(
                worker, OPERATIONS_PER_WORKER, pattern, prefix
            ),
            range(workers)
        ))
    expected = workers*OPERATIONS_PER_WORKER
    ref_rows = [row for group in sqlite_results for row in group]
    pg_rows = [row for group in postgres_results for row in group]
    assert len(ref_rows) == len(pg_rows) == expected
    assert all(row["status"] == "COMMITTED" for row in ref_rows)
    assert all(row["status"] == "COMMITTED" for row in pg_rows)

    ref_state = original_snapshot()
    pg_state = candidate_snapshot()
    assert ref_state == pg_state, (
        "Persisted contract diverged", pattern, workers,
        ref_state, pg_state
    )
    oracle = verify()
    assert len(oracle) == 7 and all(oracle.values()), oracle
    assert len(pg_state["accounts"]) == 16
    assert len(pg_state["operations"]) == expected
    assert len(pg_state["postings"]) == expected*2
    assert len(pg_state["outbox"]) == expected
    return {
        "pattern": pattern,
        "workers": workers,
        "operationsPerWorker": OPERATIONS_PER_WORKER,
        "operations": expected,
        "referenceCommitted": sum(r["status"] == "COMMITTED" for r in ref_rows),
        "postgresCommitted": sum(r["status"] == "COMMITTED" for r in pg_rows),
        "referenceBusyRetryCount": sum(r["retries"] for r in ref_rows),
        "postgresRetryCount": sum(r["retries"] for r in pg_rows),
        "persistedParity": True,
        "accountCount": len(pg_state["accounts"]),
        "operationCount": len(pg_state["operations"]),
        "postingCount": len(pg_state["postings"]),
        "outboxCount": len(pg_state["outbox"]),
        "oracle": oracle
    }


def main():
    assert SQLITE_DLL.is_file() and POSTGRES_DLL.is_file(), (
        "Build the two .NET 10 candidates before running this test"
    )
    started = time.perf_counter()
    cases = [execute_case(pattern, workers)
             for pattern in PATTERNS for workers in WORKER_COUNTS]
    assert len(cases) == 8
    total = sum(c["operations"] for c in cases)
    assert total == 2*OPERATIONS_PER_WORKER*sum(WORKER_COUNTS) == 960

    report = {
        "schemaVersion": 1,
        "experiment": "E1b-multiprocess-logical-parity",
        "status": "PASS",
        "classification": "SYNTHETIC_CONCURRENT_CONTRACT_NOT_THROUGHPUT",
        "controls": {
            "allReferenceWorkersCompleted": "PASS",
            "sameLogicalRequests": "PASS",
            "samePersistedStatePerCase": "PASS",
            "allAccountAndLedgerOracles": "PASS"
        },
        "referenceWorkerCounts": list(WORKER_COUNTS),
        "referencePatterns": list(PATTERNS),
        "operationsPerWorker": OPERATIONS_PER_WORKER,
        "totalLogicalOperations": total,
        "cases": cases,
        "sourceSha256": {
            str(path.relative_to(LAB)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                LAB / "Bank/Program.cs", LAB / "bank_test.py",
                HERE / "PgBank/Program.cs", HERE / "test_reference_parity.py",
                HERE / "test_multiprocess_parity.py", HERE / "oracle.py"
            )
        },
        "environment": {
            "platform": platform.platform(),
            "dotnetSdk": subprocess.check_output(
                [DOTNET, "--version"], text=True
            ).strip()
        },
        "elapsedHarnessSeconds": round(time.perf_counter()-started, 3),
        "limits": (
            "Comparable synthetic business operations and persisted state only. "
            "SQLite's long-lived worker processes and PostgreSQL's per-transfer "
            "process launches differ. Not a throughput, latency, Azure, WAN, "
            "SQL Server, power-failure or mainframe-capacity benchmark."
        )
    }
    (OUT / "multiprocess-parity-summary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
