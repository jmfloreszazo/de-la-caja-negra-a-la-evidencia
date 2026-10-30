#!/usr/bin/env python3
"""E1c synthetic SQL Server 2022 parity, isolation and failure tests.

This script resets E1SqlLab and must only target a disposable loopback
instance created for the experiment. No customer data or production SLA.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import time

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
OUT = LAB / "results" / "e1c"
OUT.mkdir(parents=True, exist_ok=True)
DOTNET = os.environ.get("DOTNET", "dotnet")
SQL = HERE / "SqlBank/bin/Release/net10.0/SqlBank.dll"
ORACLE = HERE / "SqlOracle/bin/Release/net10.0/SqlOracle.dll"
FIXTURES = HERE / "SqlFixtures/bin/Release/net10.0/SqlFixtures.dll"
REF = LAB / "Bank/bin/Release/net10.0/Bank.dll"
REF_DB = OUT / "reference.db"
SELECTS = {
    "accounts": "SELECT id,balance FROM accounts ORDER BY id",
    "operations": "SELECT id,src,dst,amount,status FROM operations ORDER BY id",
    "postings": "SELECT op,account,delta FROM postings ORDER BY op,account",
    "outbox": "SELECT op,event FROM outbox ORDER BY op",
}
CONTROLS = {}
CASES = []


def cli(dll, *args, expected=0, timeout=70, extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [DOTNET, str(dll), *map(str, args)],
        capture_output=True, text=True, timeout=timeout, env=env
    )
    assert result.returncode == expected, (
        str(dll), args, result.returncode, result.stdout, result.stderr
    )
    text = result.stdout.strip()
    return json.loads(text) if text.startswith(("{", "[")) else text


def fixture(*args):
    return cli(FIXTURES, *args, extra_env={
        "E1_SQL_TEST_ADMIN": "YES_DISPOSABLE"
    })


def reference_snapshot():
    with sqlite3.connect(REF_DB) as conn:
        return {
            name: [list(row) for row in conn.execute(sql)]
            for name, sql in SELECTS.items()
        }


def candidate_snapshot():
    return cli(SQL, "snapshot")


def oracle(expected=True):
    outcome = cli(ORACLE)
    checks = outcome["checks"]
    assert len(checks) == 7 and all(isinstance(v, bool) for v in checks.values())
    assert all(checks.values()) is expected, outcome
    assert outcome["status"] == ("PASS" if expected else "REJECTED")
    return checks


def reset():
    for suffix in ("", "-wal", "-shm"):
        Path(str(REF_DB) + suffix).unlink(missing_ok=True)
    cli(REF, "init", REF_DB, 16)
    cli(SQL, "init", HERE / "schema.sql")


def compare(label):
    expected = reference_snapshot()
    actual = candidate_snapshot()
    assert actual == expected, {"case": label, "reference": expected,
                                "candidate": actual}
    checks = oracle()
    return {
        "name": label,
        "persistedParity": True,
        "counts": {name: len(rows) for name, rows in actual.items()},
        "oracle": checks
    }


def sequential_contract():
    reset()
    requests = [
        ("commit", "first", 1, 2, 100, None, 0, "COMMITTED"),
        ("duplicate-commit", "first", 1, 2, 100, None, 0, "DUPLICATE_COMMITTED"),
        ("id-conflict", "first", 1, 2, 101, None, 0, "ID_CONFLICT"),
        ("overdraft", "poor", 1, 2, 200000, None, 0, "REJECTED"),
        ("duplicate-rejected", "poor", 1, 2, 200000, None, 0, "DUPLICATE_REJECTED"),
        ("conflict-rejected", "poor", 1, 2, 200001, None, 0, "ID_CONFLICT"),
        ("invalid-id", "invalid op", 1, 2, 1, None, 5, None),
        ("invalid-amount", "zero", 1, 2, 0, None, 5, None),
        ("invalid-self", "self", 1, 1, 1, None, 5, None),
        ("invalid-account", "missing", 17, 2, 1, None, 5, None),
        ("exception-rollback", "throw", 2, 1, 10, "throw-after-debit", 5, None),
        ("process-crash", "crash", 2, 1, 10, "crash-after-debit", 91, None),
        ("lost-response", "lost", 2, 1, 10, "lost-response", 92, None),
        ("lost-response-replay", "lost", 2, 1, 10, None, 0, "DUPLICATE_COMMITTED"),
        ("exception-retry", "throw", 2, 1, 10, None, 0, "COMMITTED"),
        ("crash-retry", "crash", 2, 1, 10, None, 0, "COMMITTED"),
    ]
    for label, op, src, dst, amt, fault, code, verdict in requests:
        ref_args = ["transfer", REF_DB, op, src, dst, amt]
        sql_args = ["transfer", op, src, dst, amt]
        if fault:
            ref_args.append(fault)
            sql_args.extend(["--fault", fault])
        ref = cli(REF, *ref_args, expected=code)
        actual = cli(SQL, *sql_args, expected=code)
        assert (ref if isinstance(ref, dict) else {}).get("status") == verdict
        assert (actual if isinstance(actual, dict) else {}).get("status") == verdict
        CASES.append(compare(label))
    CONTROLS["sequentialCrossEngineParity"] = "PASS"


def concurrency_and_faults():
    reset()
    def transfer(op, src, dst, amount):
        return cli(SQL, "transfer", op, src, dst, amount)
    with ThreadPoolExecutor(max_workers=2) as pool:
        race = list(pool.map(
            lambda i: transfer(f"race-{i}", 1, 2, 70000), range(2)
        ))
    assert sorted(x["status"] for x in race) == ["COMMITTED", "REJECTED"], race

    with ThreadPoolExecutor(max_workers=4) as pool:
        repeats = list(pool.map(
            lambda _: transfer("same-id", 2, 1, 100), range(4)
        ))
    assert sum(x["status"] == "COMMITTED" for x in repeats) == 1
    assert sum(x["status"] == "DUPLICATE_COMMITTED" for x in repeats) == 3
    assert transfer("same-id", 2, 1, 101)["status"] == "ID_CONFLICT"
    oracle()
    CONTROLS["overdraftAndIdempotencyUnderConcurrency"] = "PASS"

    # A deliberate duplicate INSERT must be rejected by SQL Server itself,
    # independently of the request-ID application lock.
    unique = fixture("unique-key")
    assert unique["status"] == "UNIQUE_KEY_REJECTED"
    assert unique["sqlServerError"] in (2601, 2627)
    oracle()
    CONTROLS["databaseUniqueKeyConstraint"] = "PASS"

    # SqlClient command cancellation (-2) is distinct from SET LOCK_TIMEOUT
    # (SQL Server error 1222)..
    command_timeout = fixture("command-timeout")
    assert command_timeout == {"status": "COMMAND_TIMEOUT", "sqlClientError": -2}
    oracle()
    CONTROLS["boundedSqlClientCommandTimeout"] = "PASS"

    # The fixture holds a real SQL Server UPDLOCK. Observe the lock acquired
    # before issuing the transfer; do not infer contention from elapsed time.
    def hold(account, milliseconds):
        env = os.environ.copy()
        proc = subprocess.Popen(
            [DOTNET, str(SQL), "hold-account", str(account), str(milliseconds)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=env
        )
        assert proc.stdout is not None
        assert proc.stdout.readline().strip() == "LOCKED", (
            proc.poll(), proc.stderr.read() if proc.poll() is not None else ""
        )
        return proc

    locked = hold(5, 1800)
    try:
        released = transfer("released", 5, 6, 10)
    finally:
        locked.communicate(timeout=25)
    assert released["status"] == "COMMITTED", released
    assert 1222 in released["retrySqlErrors"], released
    assert transfer("released", 5, 6, 10)["status"] == "DUPLICATE_COMMITTED"
    CONTROLS["lockReleasedDuringRetry"] = "PASS"

    locked = hold(5, 10500)
    try:
        exhausted = cli(SQL, "transfer", "exhausted", 5, 6, 10,
                        expected=7, timeout=40)
        assert exhausted["status"] == "RETRY_EXHAUSTED", exhausted
        assert len(exhausted["retrySqlErrors"]) == 6, exhausted
        assert set(exhausted["retrySqlErrors"]) == {1222}, exhausted
        assert not any(row[0] == "exhausted"
                       for row in candidate_snapshot()["operations"])
        assert not any(row[0] == "exhausted"
                       for row in candidate_snapshot()["postings"])
    finally:
        locked.terminate()
        locked.communicate(timeout=15)
    assert transfer("exhausted", 5, 6, 10)["status"] == "COMMITTED"
    assert transfer("exhausted", 5, 6, 10)["status"] == "DUPLICATE_COMMITTED"
    oracle()
    CONTROLS["boundedLockTimeoutAndRecovery"] = "PASS"

    # Test-only mutation is done by a separate tool; the SQL oracle remains
    # compiled separately and executes SELECT statements only.
    before = oracle()
    deleted = fixture("corrupt")
    corrupted = oracle(expected=False)
    assert corrupted["twoPostingsPerCommit"] is False
    assert corrupted["projectionAgrees"] is False
    assert corrupted["balancedPostings"] is False
    fixture("restore", deleted["op"], deleted["account"], deleted["delta"])
    restored = oracle()
    assert before == restored
    CONTROLS["independentOracleRejectsCorruption"] = "PASS"
    return {"race": race, "lockReleased": released,
            "lockExhaustion": exhausted, "oracleVectors": {
                "before": before, "corrupted": corrupted, "restored": restored
            }}


def deadlock_and_isolation():
    reset()
    def crossing(which):
        src, dst = (3, 4) if which == 0 else (4, 3)
        return cli(SQL, "transfer", f"deadlock-{which}", src, dst, 100,
                   "--lock-order", "source-first", "--pause-first-lock", "1200",
                   timeout=75)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(crossing, (0, 1)))
    assert all(x["status"] == "COMMITTED" for x in results), results
    assert any(1205 in x["retrySqlErrors"] for x in results), results
    oracle()
    CONTROLS["deadlock1205WholeTransactionRetry"] = "PASS"

    anomaly = {}
    for isolation in ("snapshot", "serializable"):
        fixture("reset-duty")
        with ThreadPoolExecutor(max_workers=2) as pool:
            row = list(pool.map(
                lambda ident: fixture("disable-duty", ident, isolation),
                (1, 2)
            ))
        remaining = fixture("duty-count")["remainingActive"]
        anomaly[isolation] = {"results": row, "remainingActive": remaining}
    assert anomaly["snapshot"]["remainingActive"] == 0, anomaly
    assert anomaly["serializable"]["remainingActive"] >= 1, anomaly
    assert any(1205 in item["retrySqlErrors"]
               for item in anomaly["serializable"]["results"]), anomaly
    CONTROLS["snapshotWriteSkewAndSerializableDefense"] = "PASS"
    assert fixture("pool")["status"] == "POOL_EXHAUSTED"
    CONTROLS["boundedSqlClientPool"] = "PASS"
    return {"deadlock": results, "isolation": anomaly}


def main():
    began = time.perf_counter()
    for filename in ("SqlBank", "SqlOracle", "SqlFixtures"):
        assert (HERE / filename / "bin/Release/net10.0" /
                (filename + ".dll")).is_file(), filename
    assert REF.is_file()
    sequential_contract()
    faults = concurrency_and_faults()
    isolation = deadlock_and_isolation()
    report = {
        "schemaVersion": 1, "experiment": "E1c-SQL-Server-2022",
        "classification": "EXECUTED_SYNTHETIC_SQLSERVER_NOT_MAINFRAME",
        "status": "PASS",
        "controls": CONTROLS,
        "sequentialCases": CASES,
        "observations": {"faults": faults, **isolation},
        "sourceSha256": {
            str(p.relative_to(LAB)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                HERE / "schema.sql", HERE / "SqlBank/Program.cs",
                HERE / "SqlBank/SqlBank.csproj", HERE / "SqlOracle/Program.cs",
                HERE / "SqlFixtures/Program.cs", HERE / "test_e1c.py",
                LAB / "Bank/Program.cs"
            )
        },
        "environment": {
            "sqlServerVersion": cli(SQL, "version"),
            "sqliteVersion": sqlite3.sqlite_version,
            "dotnetSdk": subprocess.check_output(
                [DOTNET, "--version"], text=True).strip(),
            "platform": platform.platform()
        },
        "elapsedSeconds": round(time.perf_counter()-began, 3),
        "limitations": (
            "Disposable, one-runner synthetic SQL Server Developer edition. "
            "No customer data, production power-loss or failover testing, "
            "mainframe throughput, external messaging or vendor TCO."
        )
    }
    (OUT / "e1c-summary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
