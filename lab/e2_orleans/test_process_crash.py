#!/usr/bin/env python3
"""E2 process-death control: kill the actual co-hosted Orleans/.NET process.

This is a real SIGKILL of a *single local process*, before/after a real
PostgreSQL commit. It is NOT a multi-silo failover or distributed crash test.
A read-only E1 accounting oracle verifies the persisted independent ledger.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
OUT = LAB / "results/e2"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(LAB / "e1_pg"))
from ledger import connect, reset
from oracle import verify
from test_e2 import APP, scenario, command, postgres_snapshot

ROUTES = ("direct", "orleans")


def invoke_and_kill(route, item):
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".json", dir=OUT,
        prefix="e2-kill-", delete=False
    ) as fd:
        json.dump({"route": route, "concurrent": False,
                   "commands": [item]}, fd)
        name = Path(fd.name)
    try:
        child = subprocess.run(
            ["dotnet", str(APP), "run", str(name)],
            capture_output=True, text=True, timeout=50,
            env=os.environ.copy()
        )
    finally:
        name.unlink(missing_ok=True)
    assert child.returncode in (-9, 137), (
        "Expected actual killed process, not an exception/clean return",
        route, item["fault"], child.returncode,
        child.stdout[-800:], child.stderr[-800:]
    )
    return child.returncode


def counts(op):
    with connect() as db:
        return {
            "operations": db.execute(
                "SELECT COUNT(*) FROM operations WHERE id=%s", (op,)
            ).fetchone()[0],
            "postings": db.execute(
                "SELECT COUNT(*) FROM postings WHERE op=%s", (op,)
            ).fetchone()[0],
            "outbox": db.execute(
                "SELECT COUNT(*) FROM outbox WHERE op=%s", (op,)
            ).fetchone()[0]
        }


def check_oracle():
    x = verify()
    assert len(x) == 7 and all(x.values()), x
    return x


def test_kills():
    results = []
    for route in ROUTES:
        for fault in ("kill-before-commit", "kill-after-commit"):
            reset()
            op = f"e2-{route}-{fault}"
            original = postgres_snapshot()
            item = command(op, 3, 4, 42, fault)
            exit_code = invoke_and_kill(route, item)
            state = counts(op)
            expected = {"operations": 0, "postings": 0, "outbox": 0}                 if fault == "kill-before-commit"                 else {"operations": 1, "postings": 2, "outbox": 1}
            assert state == expected, (route, fault, state)
            if fault == "kill-before-commit":
                assert original == postgres_snapshot()
            checks = check_oracle()
            recovered = scenario(route, [command(op, 3, 4, 42)])
            status = "COMMITTED" if fault == "kill-before-commit"                 else "DUPLICATE_COMMITTED"
            assert recovered[0]["status"] == status, recovered
            assert scenario(route, [command(op, 3, 4, 42)])[0][
                "status"] == "DUPLICATE_COMMITTED"
            assert counts(op) == {
                "operations": 1, "postings": 2, "outbox": 1
            }
            check_oracle()
            results.append({
                "route": route, "fault": fault, "exitCode": exit_code,
                "afterKill": state, "recoveryStatus": status,
                "finalExactlyOneDurableEffect": True,
                "independentOracle": checks
            })
    return results


def test_nonatomic_split():
    # Isolated, deliberately UNSAFE mutation mimics credit/debit split
    # across independent transactions. Never used by AccountGrain.
    reset()
    before = check_oracle()
    try:
        with connect() as db:
            db.execute(
                "UPDATE accounts SET balance=balance-42 WHERE id=3")
        bad = verify()
        assert bad["conserved"] is False, bad
        assert bad["projectionAgrees"] is False, bad
        assert bad["balancedPostings"] is True, bad
    finally:
        with connect() as db:
            db.execute(
                "UPDATE accounts SET balance=balance+42 WHERE id=3")
    after = check_oracle()
    assert after == before
    return {"before": before, "unsafeSplit": bad, "restored": after}


def main():
    assert APP.is_file(), "Build the .NET 10 Orleans lab first"
    kills = test_kills()
    negative = test_nonatomic_split()
    assert len(kills) == 4
    report = {
        "schemaVersion": 1,
        "experiment": "E2-Orleans-Actual-Cohost-Process-Kill",
        "status": "PASS",
        "classification": "SYNTHETIC_SINGLE_COHOST_SIGKILL_NOT_MULTISILO_FAILOVER",
        "controls": {
            "actualProcessSIGKILLBeforeAndAfterCommit": "PASS",
            "rollbackOnDatabaseSessionDeath": "PASS",
            "postCommitAmbiguityResolvesByOperationId": "PASS",
            "exactlyOneDurablePostingAndOutbox": "PASS",
            "isolatedNonAtomicSplitRejectedByIndependentOracle": "PASS"
        },
        "killedRuns": kills,
        "negativeSplit": negative,
        "sourceSha256": {
            str(path.relative_to(LAB)): hashlib.sha256(
                path.read_bytes()).hexdigest()
            for path in (
                HERE / "test_process_crash.py",
                HERE / "OrleansLab/PgDurableLedger.cs",
                HERE / "OrleansLab/Program.cs",
                HERE / "OrleansLab/Contracts.cs",
                LAB / "e1_pg/oracle.py"
            )
        },
        "limitations": (
            "Actual hard termination of the same local process hosting a "
            "single Orleans silo and .NET client. No real multi-silo "
            "reassignment, leader election, network partition, storage "
            "power loss, or banking mainframe equivalence. The deliberately "
            "unsafe split writes are a separate SQL fixture, not actor code."
        )
    }
    (OUT / "e2-process-crash.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
