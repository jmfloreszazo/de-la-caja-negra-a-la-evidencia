#!/usr/bin/env python3
"""Cross-engine E1b contract parity against the unchanged .NET/SQLite reference.

Run ONLY against the disposable E1_PG_DSN database: reset() drops test tables.
This validates synthetic accounting semantics, never throughput or mainframe scale.
"""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time

from ledger import connect, reset
from oracle import verify

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
OUT = LAB / "results" / "e1"
OUT.mkdir(parents=True, exist_ok=True)
DOTNET = os.environ.get("DOTNET", "dotnet")
SQLITE_DLL = LAB / "Bank/bin/Release/net10.0/Bank.dll"
POSTGRES_DLL = HERE / "PgBank/bin/Release/net10.0/PgBank.dll"
SQLITE_DB = OUT / "reference-parity.db"
TABLES = {
    "accounts": "SELECT id,balance FROM accounts ORDER BY id",
    "operations": "SELECT id,src,dst,amount,status FROM operations ORDER BY id",
    "postings": "SELECT op,account,delta FROM postings ORDER BY op,account",
    "outbox": "SELECT op,event FROM outbox ORDER BY op",
}


def command(args, expected_code=0):
    result = subprocess.run([DOTNET, *map(str, args)], capture_output=True,
                            text=True, timeout=40, env=os.environ)
    assert result.returncode == expected_code, (
        args, result.returncode, result.stdout, result.stderr
    )
    if result.stdout.strip().startswith("{"):
        return json.loads(result.stdout)
    return None


def sqlite_transfer(op, src, dst, amount, fault="none", expected_code=0):
    args = [SQLITE_DLL, "transfer", SQLITE_DB, op, src, dst, amount]
    if fault != "none":
        args.append(fault)
    return command(args, expected_code)


def postgres_transfer(op, src, dst, amount, fault="none", expected_code=0):
    args = [POSTGRES_DLL, "transfer", op, src, dst, amount]
    if fault != "none":
        args.extend(["--fault", fault])
    return command(args, expected_code)


def original_snapshot():
    with sqlite3.connect(SQLITE_DB) as db:
        return {name: db.execute(sql).fetchall() for name, sql in TABLES.items()}


def candidate_snapshot():
    with connect() as db:
        return {name: db.execute(sql).fetchall() for name, sql in TABLES.items()}


def compare_state(label):
    expected = original_snapshot()
    actual = candidate_snapshot()
    assert expected == actual, {
        "case": label,
        "reference": expected,
        "candidate": actual
    }
    oracle_checks = verify()
    assert all(oracle_checks.values()), (label, oracle_checks)
    return {
        "accounts": len(actual["accounts"]),
        "operations": len(actual["operations"]),
        "postings": len(actual["postings"]),
        "outbox": len(actual["outbox"]),
        "oracle": "PASS"
    }


def initialize():
    for suffix in ("", "-wal", "-shm"):
        Path(str(SQLITE_DB) + suffix).unlink(missing_ok=True)
    reset()
    command([SQLITE_DLL, "init", SQLITE_DB, 16])


def build_reference():
    result = subprocess.run([
        DOTNET, "build", str(LAB / "Bank"), "-c", "Release", "-m:1",
        "--disable-build-servers"
    ], capture_output=True, text=True, timeout=180)
    (OUT / "sqlite-reference-build.txt").write_text(
        result.stdout + result.stderr, encoding="utf-8"
    )
    assert result.returncode == 0, result.stdout + result.stderr


def run_sequence():
    # Same requests and expected process exits for the two .NET 10 programs.
    # Each step compares *all persisted tables*, not just a response status.
    steps = [
        ("accepted", "one", 1, 2, 100, "none", 0, "COMMITTED"),
        ("duplicate-commit", "one", 1, 2, 100, "none", 0, "DUPLICATE_COMMITTED"),
        ("id-conflict", "one", 1, 2, 101, "none", 0, "ID_CONFLICT"),
        ("rejected", "poor", 1, 2, 200000, "none", 0, "REJECTED"),
        ("duplicate-rejection", "poor", 1, 2, 200000, "none", 0,
         "DUPLICATE_REJECTED"),
        ("rejection-conflict", "poor", 1, 2, 200001, "none", 0, "ID_CONFLICT"),
        ("invalid-operation-id", "invalid op", 1, 2, 1, "none", 5, None),
        ("invalid-zero", "zero", 1, 2, 0, "none", 5, None),
        ("invalid-self-transfer", "self", 1, 1, 1, "none", 5, None),
        ("invalid-account", "missing", 17, 2, 1, "none", 5, None),
        ("exception-rollback", "fault-exception", 2, 1, 10,
         "throw-after-debit", 5, None),
        ("process-crash-rollback", "fault-crash", 2, 1, 10,
         "crash-after-debit", 91, None),
        ("lost-acknowledgment", "fault-lost", 2, 1, 10,
         "lost-response", 92, None),
        ("idempotent-replay", "fault-lost", 2, 1, 10,
         "none", 0, "DUPLICATE_COMMITTED"),
        ("retry-exception-operation", "fault-exception", 2, 1, 10,
         "none", 0, "COMMITTED"),
        ("retry-crashed-operation", "fault-crash", 2, 1, 10,
         "none", 0, "COMMITTED"),
    ]
    results = []
    for label, op, src, dst, amount, fault, exit_code, status in steps:
        before = original_snapshot()
        ref = sqlite_transfer(op, src, dst, amount, fault, exit_code)
        pg = postgres_transfer(op, src, dst, amount, fault, exit_code)
        assert (ref or {}).get("status") == status, (label, ref, status)
        assert (pg or {}).get("status") == status, (label, pg, status)
        state = compare_state(label)
        if exit_code in (5, 91):
            assert original_snapshot() == before, (label, "unexpected mutation")
        results.append({
            "case": label,
            "exitCode": exit_code,
            "expectedStatus": status,
            "persistedParity": True,
            **state
        })
    return results


def blocked_then_released():
    # Mirror the SQLite reference's BEGIN IMMEDIATE lock-release case.
    sqlite_holder = sqlite3.connect(SQLITE_DB)
    sqlite_holder.execute("BEGIN IMMEDIATE")
    ref = subprocess.Popen(
        [DOTNET, str(SQLITE_DLL), "transfer", str(SQLITE_DB),
         "unblocked", "5", "6", "10"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    try:
        time.sleep(0.55)
    finally:
        sqlite_holder.rollback()
        sqlite_holder.close()
    ref_stdout, ref_stderr = ref.communicate(timeout=30)
    assert ref.returncode == 0, (ref.returncode, ref_stdout, ref_stderr)
    ref_result = json.loads(ref_stdout)
    assert ref_result["status"] == "COMMITTED", ref_result
    assert ref_result["retries"] >= 1, ref_result

    # PostgreSQL holds an account row lock while the .NET candidate retries
    # the full SQL transaction after its own 750ms lock timeout.
    with connect() as holder:
        with holder.transaction():
            holder.execute("SELECT id FROM accounts WHERE id=5 FOR UPDATE")
            pg = subprocess.Popen(
                [DOTNET, str(POSTGRES_DLL), "transfer",
                 "unblocked", "5", "6", "10"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env=os.environ
            )
            saw_wait = False
            until = time.monotonic() + 8
            while time.monotonic() < until:
                with connect() as observer:
                    blocked = observer.execute(
                        "SELECT COUNT(*) FROM pg_stat_activity "
                        "WHERE pid<>pg_backend_pid() AND wait_event_type='Lock' "
                        "AND query LIKE '%accounts%FOR UPDATE%'"
                    ).fetchone()[0]
                if blocked:
                    saw_wait = True
                    break
                assert pg.poll() is None, "candidate exited before lock observation"
                time.sleep(0.03)
            assert saw_wait, "did not observe PostgreSQL candidate awaiting a row lock"
            time.sleep(0.85)  # force at least one genuine 55P03 in candidate
        # The transaction end releases the row lock and the candidate can commit.
    stdout, stderr = pg.communicate(timeout=30)
    assert pg.returncode == 0, (pg.returncode, stdout, stderr)
    result = json.loads(stdout)
    assert result["status"] == "COMMITTED", result
    assert result["retries"] >= 1, result
    assert "55P03" in result["retry_sqlstates"], result
    state = compare_state("released-after-timeout")
    assert postgres_transfer("unblocked", 5, 6, 10)["status"] == "DUPLICATE_COMMITTED"
    assert sqlite_transfer("unblocked", 5, 6, 10)["status"] == "DUPLICATE_COMMITTED"
    compare_state("replayed-after-unblock")
    return {
        "referenceRetriesObserved": ref_result["retries"] >= 1,
        "postgresRetrySqlstate": "55P03",
        "candidateRetryCount": result["retries"],
        "persistedParity": True,
        **state
    }


def main():
    started = time.perf_counter()
    build_reference()
    assert POSTGRES_DLL.is_file(), "Run test_dotnet.py first to build the candidate"
    initialize()
    cases = run_sequence()
    unblock = blocked_then_released()
    with connect() as db:
        postgres_version = db.execute("SHOW server_version").fetchone()[0]
    summary = {
        "schemaVersion": 1,
        "experiment": "E1b-reference-parity",
        "status": "PASS",
        "classification": "SYNTHETIC_FUNCTIONAL_PARITY_NOT_CAPACITY",
        "controls": {
            "sequentialReferenceParity": "PASS",
            "invalidInputNoMutation": "PASS",
            "duplicateRejectionAndConflict": "PASS",
            "faultRecoveryAndAmbiguousCommit": "PASS",
            "lockReleaseUnderRetry": "PASS",
            "persistedIndependentOracle": "PASS"
        },
        "cases": cases,
        "lockRelease": unblock,
        "sourceSha256": {
            str(path.relative_to(LAB)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [
                LAB / "Bank/Program.cs", LAB / "Bank/Bank.csproj",
                HERE / "PgBank/Program.cs", HERE / "PgBank/PgBank.csproj",
                HERE / "test_reference_parity.py"
            ]
        },
        "environment": {
            "postgresVersion": postgres_version,
            "sqliteVersion": sqlite3.sqlite_version,
            "dotnetVersion": subprocess.check_output(
                [DOTNET, "--version"], text=True
            ).strip()
        },
        "elapsedSeconds": round(time.perf_counter()-started, 3),
        "limits": (
            "Disposable, single-runner synthetic functional comparison: "
            "not a multi-process workload or performance parity test; "
            "not SQL Server, CICS, Db2, Azure, WAN or mainframe equivalence."
        )
    }
    (OUT / "reference-parity-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
