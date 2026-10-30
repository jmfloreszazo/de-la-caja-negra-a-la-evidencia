#!/usr/bin/env python3
"""E1c SQL Server and SQLite reference worker-matrix functional parity.

Runs 1/2/4/8 workers × 32 operations each for uniform and hot accounts.
The SQLite reference retains long-lived worker processes while SQL Server
launches one independent .NET CLI transfer process per operation. No
throughput or latency equality can be inferred from the different models.
All databases and transfer records are synthetic and disposable.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

from test_e1c import (
    HERE, LAB, OUT, DOTNET, SQL, REF, REF_DB,
    cli, reset, reference_snapshot, candidate_snapshot, oracle
)

WORKERS = (1, 2, 4, 8)
PATTERNS = ("uniform", "hot")
COUNT = 32


def sqlite_worker(worker, workers, pattern):
    proc = subprocess.run(
        [DOTNET, str(REF), "worker", str(REF_DB),
         str(worker), str(COUNT), pattern, "load"],
        capture_output=True, text=True, timeout=150
    )
    assert proc.returncode == 0, (
        "SQLite worker", pattern, workers, worker,
        proc.returncode, proc.stdout, proc.stderr
    )
    rows = json.loads(proc.stdout)
    assert len(rows) == COUNT and all(
        row["status"] == "COMMITTED" for row in rows
    ), rows
    return rows


def sql_worker(worker, workers, pattern):
    # Match the SQLite reference's one long-lived CLI process per worker.
    # Each transfer still owns its own SQL Server local transaction.
    rows = cli(SQL, "worker", worker, COUNT, pattern, "load", timeout=150)
    assert isinstance(rows, list) and len(rows) == COUNT, (
        "SQL Server worker output", pattern, workers, worker, rows
    )
    assert all(row["status"] == "COMMITTED" for row in rows), rows
    return rows


def run_case(pattern, workers):
    reset()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        sqlite_rows = list(pool.map(
            lambda worker: sqlite_worker(worker, workers, pattern),
            range(workers)
        ))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        sql_rows = list(pool.map(
            lambda worker: sql_worker(worker, workers, pattern),
            range(workers)
        ))
    expected = workers*COUNT
    assert sum(len(x) for x in sqlite_rows) == expected
    assert sum(len(x) for x in sql_rows) == expected
    reference = reference_snapshot()
    observed = candidate_snapshot()
    assert reference == observed, (
        "Persisted reference mismatch", pattern, workers, reference, observed
    )
    checks = oracle()
    assert len(checks) == 7 and all(checks.values())
    assert len(observed["accounts"]) == 16
    assert len(observed["operations"]) == expected
    assert len(observed["postings"]) == expected*2
    assert len(observed["outbox"]) == expected
    return {
        "pattern": pattern,
        "workers": workers,
        "operationsPerWorker": COUNT,
        "operations": expected,
        "referenceCommitted": expected,
        "sqlServerCommitted": expected,
        "referenceBusyRetries": sum(r["retries"] for group in sqlite_rows
                                    for r in group),
        "sqlServerRetries": sum(r["retries"] for group in sql_rows
                                for r in group),
        "persistedParity": True,
        "accounts": len(observed["accounts"]),
        "operationsPersisted": len(observed["operations"]),
        "postings": len(observed["postings"]),
        "outbox": len(observed["outbox"]),
        "oracle": checks
    }


def main():
    started = time.perf_counter()
    assert SQL.is_file() and REF.is_file(), "Build .NET projects before testing"
    cases = [run_case(pattern, workers)
             for pattern in PATTERNS for workers in WORKERS]
    total = sum(row["operations"] for row in cases)
    assert total == 960 and len(cases) == 8
    result = {
        "schemaVersion": 1,
        "experiment": "E1c-SQLServer-Worker-Parity",
        "status": "PASS",
        "classification": "SYNTHETIC_ACCOUNTING_WORKLOAD_NOT_CAPACITY",
        "controls": {
            "eightUniformHotWorkerCases": "PASS",
            "bothCandidatesCommitAll960": "PASS",
            "completeFourTableParity": "PASS",
            "sevenIndependentOracleInvariants": "PASS"
        },
        "workerCounts": list(WORKERS),
        "patterns": list(PATTERNS),
        "operationsPerWorker": COUNT,
        "totalLogicalOperations": total,
        "cases": cases,
        "sourceSha256": {
            str(f.relative_to(LAB)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in (
                LAB/"Bank/Program.cs", LAB/"bank_test.py",
                HERE/"SqlBank/Program.cs", HERE/"SqlOracle/Program.cs",
                HERE/"test_e1c.py", HERE/"test_worker_parity.py"
            )
        },
        "environment": {
            "sqlServerVersion": cli(SQL, "version"),
            "dotnetSdk": subprocess.check_output(
                [DOTNET, "--version"], text=True).strip(),
            "platform": platform.platform()
        },
        "elapsedHarnessSeconds": round(time.perf_counter()-started, 3),
        "limitations": (
            "Only business outcomes and persisted account/operation/posting/outbox "
            "state are compared. SQLite uses long-lived worker processes and "
            "SQL Server launches a new .NET CLI for each transfer. No throughput "
            "or tail latency comparison, power loss, SQL Server HA, Azure SQL "
            "or mainframe capacity equivalence."
        )
    }
    (OUT/"e1c-worker-parity-summary.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
