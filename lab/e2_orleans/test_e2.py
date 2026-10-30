#!/usr/bin/env python3
"""E2-F01/F02/F03: real Orleans co-hosted grain, E1 SQL and SQLite contract.

The account grain only queues requests; PostgreSQL owns all four persisted
tables in one transaction. Synthetic local tests are NOT an Orleans capacity
or distributed failure benchmark. Source and reference candidates are not edited.
"""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
OUT = LAB / "results" / "e2"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(LAB / "e1_pg"))
from ledger import connect, reset  # noqa: E402
from oracle import verify  # noqa: E402

DOTNET = os.getenv("DOTNET", "dotnet")
APP = HERE / "OrleansLab/bin/Release/net10.0/OrleansLab.dll"
BASELINE = LAB / "Bank/bin/Release/net10.0/Bank.dll"
PG_BASELINE = LAB / "e1_pg/PgBank/bin/Release/net10.0/PgBank.dll"
SQLITE_FILE = OUT / "e2-reference.db"
TABLES = {
    "accounts": "SELECT id,balance FROM accounts ORDER BY id",
    "operations": "SELECT id,src,dst,amount,status FROM operations ORDER BY id",
    "postings": "SELECT op,account,delta FROM postings ORDER BY op,account",
    "outbox": "SELECT op,event FROM outbox ORDER BY op",
}


def invoke(exe, *args, code=0, timeout=100):
    proc = subprocess.run([DOTNET, str(exe), *map(str, args)],
                          capture_output=True, text=True, timeout=timeout, env=os.environ)
    assert proc.returncode == code, (
        "Unexpected exit", str(exe), args, proc.returncode, proc.stderr,
        proc.stdout[-3000:]
    )
    return json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else None


def command(op, src, dst, amount, fault="none"):
    return {
        "operationId": op, "sourceAccountId": src, "targetAccountId": dst,
        "amountCents": amount, "fault": fault
    }


def oracle():
    checks = verify()
    assert len(checks) == 7, checks
    assert all(checks.values()), checks
    return checks


def postgres_snapshot():
    with connect() as db:
        return {name: db.execute(sql).fetchall() for name, sql in TABLES.items()}


def sqlite_snapshot():
    with sqlite3.connect(SQLITE_FILE) as db:
        return {name: db.execute(sql).fetchall() for name, sql in TABLES.items()}


def reset_reference():
    for suffix in ("", "-wal", "-shm"):
        Path(str(SQLITE_FILE) + suffix).unlink(missing_ok=True)
    invoke(BASELINE, "init", SQLITE_FILE, 16)


def scenario(route, cmds, concurrent=False):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json",
                                     prefix="e2-", dir=OUT, delete=False) as f:
        json.dump({"route": route, "concurrent": concurrent, "commands": cmds}, f)
        path = Path(f.name)
    try:
        result = invoke(APP, "run", path, timeout=180)
    finally:
        path.unlink(missing_ok=True)
    assert result["experiment"] == "E2-orleans-ledger"
    assert result["route"] == route
    assert result["sourceOfTruth"] == "postgresql-transaction"
    assert result["concurrent"] is concurrent
    assert len(result["results"]) == len(cmds)
    for cmd, res in zip(cmds, result["results"]):
        if res["status"] == "INVALID":
            assert res["handledBy"] == "input-validation"
        elif route == "orleans":
            assert res["handledBy"] == f"grain-{cmd['sourceAccountId']}", res
        else:
            assert res["handledBy"] == "direct-ledger", res
    return result["results"]


def baseline_sequences():
    commands = [
        ("commit", command("first", 1, 2, 100), 0, "COMMITTED"),
        ("duplicate", command("first", 1, 2, 100), 0, "DUPLICATE_COMMITTED"),
        ("identity-conflict", command("first", 1, 2, 101), 0, "ID_CONFLICT"),
        ("overdraft", command("poor", 1, 2, 200000), 0, "REJECTED"),
        ("rejected-replay", command("poor", 1, 2, 200000), 0, "DUPLICATE_REJECTED"),
        ("rejected-conflict", command("poor", 1, 2, 200001), 0, "ID_CONFLICT"),
        ("invalid-id", command("invalid op", 1, 2, 5), 5, "INVALID"),
        ("invalid-zero", command("zero", 1, 2, 0), 5, "INVALID"),
        ("invalid-self", command("self", 1, 1, 10), 5, "INVALID"),
        ("invalid-account", command("missing", 17, 1, 5), 5, "INVALID"),
        ("exception-before-commit", command("throw", 2, 1, 5, "throw-after-debit"),
         5, "INJECTED_ROLLBACK"),
        ("lost-ack-after-commit", command("lost", 2, 1, 5, "lost-response"),
         92, "AMBIGUOUS_RESPONSE"),
        ("lost-ack-replay", command("lost", 2, 1, 5), 0, "DUPLICATE_COMMITTED"),
        ("rollback-retry", command("throw", 2, 1, 5), 0, "COMMITTED"),
        ("normal-transfer", command("another", 5, 6, 12), 0, "COMMITTED"),
    ]
    summaries = []
    # First generate protected SQLite and independent E1b PostgreSQL results.
    reset()
    reset_reference()
    for label, cmd, exit_code, status in commands:
        args = [cmd["operationId"], cmd["sourceAccountId"],
                cmd["targetAccountId"], cmd["amountCents"]]
        sqlite_args = ["transfer", SQLITE_FILE, *args]
        pg_args = ["transfer", *args]
        if cmd["fault"] != "none":
            sqlite_args.append(cmd["fault"])
            pg_args.extend(("--fault", cmd["fault"]))
        ref = invoke(BASELINE, *sqlite_args, code=exit_code)
        pg = invoke(PG_BASELINE, *pg_args, code=exit_code)
        baseline_status = None if exit_code else status
        if exit_code == 0:
            assert ref["status"] == pg["status"] == baseline_status, label
        assert postgres_snapshot() == sqlite_snapshot(), ("E1 baseline mismatch", label)
        oracle()
    reference_state = sqlite_snapshot()

    for route in ("direct", "orleans"):
        reset()
        outcomes = scenario(route, [cmd for _, cmd, _, _ in commands])
        for item, result in zip(commands, outcomes):
            assert result["status"] == item[3], (route, item[0], result)
        assert postgres_snapshot() == reference_state, (route, "reference divergence")
        checks = oracle()
        summaries.append({
            "route": route, "cases": len(commands),
            "statuses": [x["status"] for x in outcomes],
            "persistedStateMatchesProtectedSQLite": True,
            "independentOracle": checks
        })
    return summaries


def concurrent_controls():
    tests = []
    for route in ("direct", "orleans"):
        reset()
        # The two disjoint operation IDs both ask to debit more than the
        # account owns in total. Exactly one is allowed to commit.
        raced = scenario(route, [
            command("race-0", 1, 2, 70000),
            command("race-1", 1, 2, 70000)
        ], concurrent=True)
        assert sorted(x["status"] for x in raced) == ["COMMITTED", "REJECTED"]
        assert all(x["status"] != "RETRY_EXHAUSTED" for x in raced)
        checks = oracle()

        duplicates = scenario(route, [
            command("one-id", 2, 1, 100) for _ in range(4)
        ], concurrent=True)
        assert sorted(x["status"] for x in duplicates) == [
            "COMMITTED", "DUPLICATE_COMMITTED",
            "DUPLICATE_COMMITTED", "DUPLICATE_COMMITTED"
        ]
        assert scenario(route, [command("one-id", 2, 1, 101)])[0]["status"] == "ID_CONFLICT"
        assert scenario(route, [command("one-id", 2, 1, 100)])[0]["status"] == "DUPLICATE_COMMITTED"
        checks = oracle()
        with connect() as db:
            committed = db.execute(
                "SELECT COUNT(*) FROM operations WHERE status='COMMITTED'").fetchone()[0]
            postings = db.execute("SELECT COUNT(*) FROM postings").fetchone()[0]
            outbox = db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
        assert (committed, postings, outbox) == (2, 4, 2)
        tests.append({
            "route": route, "overdraftStatuses": sorted(x["status"] for x in raced),
            "duplicateStatuses": sorted(x["status"] for x in duplicates),
            "committed": committed, "postings": postings, "outbox": outbox,
            "independentOracle": checks
        })
    return tests


def crossed_transfer_controls():
    """E2-F04: concurrent A->B/B->A commands, with independent SQL snapshots.

    This checks competing source-grain activations against the SAME atomic
    PostgreSQL ledger; it is not an injected 40P01 deadlock or multi-silo test.
    """
    commands = [
        command(f"cross-{index:03d}", 1 if index % 2 == 0 else 2,
                2 if index % 2 == 0 else 1, 123)
        for index in range(32)
    ]
    reports = []
    reference_state = None
    for route in ("direct", "orleans"):
        reset()
        results = scenario(route, commands, concurrent=True)
        assert len(results) == len(commands)
        assert all(row["status"] == "COMMITTED" for row in results), (route, results)
        checks = oracle()
        state = postgres_snapshot()
        with connect() as db:
            counts = {
                "operations": db.execute(
                    "SELECT COUNT(*) FROM operations WHERE status='COMMITTED'"
                ).fetchone()[0],
                "postings": db.execute(
                    "SELECT COUNT(*) FROM postings"
                ).fetchone()[0],
                "outbox": db.execute(
                    "SELECT COUNT(*) FROM outbox"
                ).fetchone()[0]
            }
            balances = db.execute(
                "SELECT id,balance FROM accounts WHERE id IN (1,2) ORDER BY id"
            ).fetchall()
        assert counts == {"operations": 32, "postings": 64, "outbox": 32}, counts
        assert balances == [(1, 100000), (2, 100000)], balances
        if reference_state is None:
            reference_state = state
        else:
            assert state == reference_state, "Crossed-transfer route ledger divergence"
        reports.append({
            "route": route, "crossedOperations": len(commands),
            "sourceAccounts": [1, 2],
            "committed": counts["operations"],
            "postings": counts["postings"],
            "outbox": counts["outbox"],
            "retrySqlStates": [
                sqlstate for row in results for sqlstate in row["retrySqlStates"]
            ],
            "persistedStateSha256": hashlib.sha256(json.dumps(
                state, separators=(",", ":"), ensure_ascii=True
            ).encode("utf-8")).hexdigest(),
            "sevenIndependentOracleInvariants": checks,
            "limitations": "Crossed requests, but no forced deadlock or multi-silo failover"
        })
    assert reports[0]["persistedStateSha256"] == reports[1]["persistedStateSha256"]
    return reports


def unsafe_reentrancy_negative():
    """E2-N02: prove a reentrant actor-local read/modify/write loses updates.

    The negative fixture deliberately uses a separate grain and no SQL
    writes. The accepted AccountGrain is non-reentrant and unchanged.
    """
    reset()
    original = postgres_snapshot()
    result = invoke(APP, "negative-reentrancy", timeout=45)
    assert result["experiment"] == "E2-Orleans-Reentrant-Unsafe-Actor-State"
    assert result["status"] == "NEGATIVE_CONTROL_DETECTED"
    assert result["concurrentCalls"] == 16
    assert result["expectedIfAtomic"] == 16
    assert result["observedActorLocalValue"] == 1
    assert result["lostUpdates"] == 15
    assert result["durableSqlTransfers"] == 0
    assert postgres_snapshot() == original, "Unsafe negative control touched SQL"
    result["independentSqlOracle"] = oracle()
    return result


def negative_oracle():
    reset()
    results = scenario("orleans", [command("neg-case", 3, 4, 42)])
    assert results[0]["status"] == "COMMITTED"
    before = oracle()
    with connect() as db:
        posting = db.execute(
            "SELECT op,account,delta FROM postings WHERE op='neg-case' "
            "ORDER BY account LIMIT 1").fetchone()
    assert posting is not None
    try:
        with connect() as db:
            db.execute("DELETE FROM postings WHERE op=%s AND account=%s",
                       (posting[0], posting[1]))
        corrupted = verify()
        assert corrupted["balancedPostings"] is False
        assert corrupted["twoPostingsPerCommit"] is False
        assert corrupted["projectionAgrees"] is False
    finally:
        with connect() as db:
            db.execute("INSERT INTO postings(op,account,delta) VALUES(%s,%s,%s)",
                       posting)
    restored = oracle()
    assert restored == before
    return {"before": before, "corrupted": corrupted, "restored": restored}


def main():
    for dll in (APP, BASELINE, PG_BASELINE):
        assert dll.is_file(), dll
    observed = {
        "schemaVersion": 1,
        "experiment": "E2-Orleans-Persistent-Ledger-Smoke",
        "classification": "SYNTHETIC_SINGLE_SILO_FUNCTIONAL_NOT_CAPACITY",
        "status": "PASS",
        "controls": {
            "sequentialProtectedSQLiteAndE1bParity": "PASS",
            "directAndGrainShareDurableLedger": "PASS",
            "concurrentOverdraftAndOperationId": "PASS",
            "crossedSourceAccountTransfers": "PASS",
            "unsafeReentrantActorStateRejected": "PASS",
            "simulatedRollbackAndLostResponseReplay": "PASS",
            "independentSqlOracleNegativeMutation": "PASS"
        },
        "functional": baseline_sequences(),
        "concurrent": concurrent_controls(),
        "crossedTransfers": crossed_transfer_controls(),
        "unsafeReentrancyNegative": unsafe_reentrancy_negative(),
        "oracleNegative": negative_oracle(),
        "sourceSha256": {
            str(x.relative_to(LAB)): hashlib.sha256(x.read_bytes()).hexdigest()
            for x in [
                LAB / "Bank/Program.cs",
                LAB / "e1_pg/PgBank/Program.cs",
                HERE / "OrleansLab/OrleansLab.csproj",
                HERE / "OrleansLab/Program.cs",
                HERE / "OrleansLab/Contracts.cs",
                HERE / "OrleansLab/UnsafeReentrancyNegative.cs",
                HERE / "OrleansLab/PgDurableLedger.cs",
                HERE / "test_e2.py",
            ]
        },
        "limitations": (
            "Real single-host co-located Orleans grain with PostgreSQL durability. "
            "Exception and lost-response controls are simulated, NOT actual silo "
            "process crash. No distributed Orleans silos, open-loop workload, "
            "5-percent-hot/50-percent-intent benchmarks, p99 or production/MIPS."
        )
    }
    (OUT / "e2-smoke.json").write_text(json.dumps(observed, indent=2) + "\n",
                                       encoding="utf-8")
    print(json.dumps(observed, indent=2))


if __name__ == "__main__":
    main()
