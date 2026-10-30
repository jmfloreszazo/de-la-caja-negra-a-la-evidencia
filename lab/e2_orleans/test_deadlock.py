#!/usr/bin/env python3
"""E2-F04: observe an actual SQLSTATE 40P01 and atomic replay in both routes.

The deadlock is deliberately forced in a tightly scoped disposable fixture;
the standard transfer path, lock order and AccountGrain are unchanged.
"""
import hashlib
import json
import os
from test_e2 import APP, HERE, LAB, OUT, command, oracle, postgres_snapshot, reset, scenario, connect

ROUTES = ("direct", "orleans")
COMMANDS = [
    command("e2-deadlock-a", 1, 2, 41, "deadlock-once"),
    command("e2-deadlock-b", 2, 1, 41, "deadlock-once"),
]


def counts():
    with connect() as db:
        return {
            "committed": db.execute(
                "SELECT COUNT(*) FROM operations WHERE status='COMMITTED'"
            ).fetchone()[0],
            "postings": db.execute("SELECT COUNT(*) FROM postings").fetchone()[0],
            "outbox": db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0],
            "balances": db.execute(
                "SELECT id,balance FROM accounts WHERE id IN (1,2) ORDER BY id"
            ).fetchall()
        }


def exercise(route):
    reset()
    before = postgres_snapshot()
    assert counts() == {
        "committed": 0, "postings": 0, "outbox": 0,
        "balances": [(1, 100000), (2, 100000)]
    }
    previous = os.environ.pop("E2_ENABLE_DEADLOCK_FIXTURE", None)
    try:
        # Verify that the dangerous path is not reachable without opt-in.
        denied = scenario(route, COMMANDS, concurrent=True)
        assert [x["status"] for x in denied] == ["INVALID", "INVALID"]
        assert postgres_snapshot() == before
        os.environ["E2_ENABLE_DEADLOCK_FIXTURE"] = "1"
        response = scenario(route, COMMANDS, concurrent=True)
    finally:
        if previous is not None:
            os.environ["E2_ENABLE_DEADLOCK_FIXTURE"] = previous
        else:
            os.environ.pop("E2_ENABLE_DEADLOCK_FIXTURE", None)

    assert [x["status"] for x in response] == ["COMMITTED", "COMMITTED"], response
    sqlstates = [state for row in response for state in row["retrySqlStates"]]
    assert sqlstates == ["40P01"], ("Expected one actual PostgreSQL deadlock victim", route, sqlstates)
    assert sum(row["retries"] for row in response) == 1, response
    state = postgres_snapshot()
    persisted = counts()
    assert persisted == {
        "committed": 2, "postings": 4, "outbox": 2,
        "balances": [(1, 100000), (2, 100000)]
    }, persisted
    checks = oracle()
    stable_replay = [
        command(x["operationId"], x["sourceAccountId"],
                x["targetAccountId"], x["amountCents"])
        for x in COMMANDS
    ]
    replay = scenario(route, stable_replay)
    assert [x["status"] for x in replay] == [
        "DUPLICATE_COMMITTED", "DUPLICATE_COMMITTED"
    ], replay
    conflict = scenario(route, [command("e2-deadlock-a", 1, 2, 42)])
    assert conflict[0]["status"] == "ID_CONFLICT"
    assert postgres_snapshot() == state
    assert oracle() == checks
    return {
        "route": route,
        "optInRequired": True,
        "statuses": [x["status"] for x in response],
        "retrySqlStates": [x["retrySqlStates"] for x in response],
        "observed40P01Victims": sqlstates.count("40P01"),
        "fullTransactionRetryRecovered": True,
        "persisted": persisted,
        "replayStatuses": [x["status"] for x in replay],
        "conflictingIdStatus": conflict[0]["status"],
        "stateSha256": hashlib.sha256(json.dumps(
            state, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")).hexdigest(),
        "independentOracle": checks
    }


def main():
    assert APP.is_file(), "Build OrleansLab in Release first"
    results = [exercise(route) for route in ROUTES]
    assert results[0]["stateSha256"] == results[1]["stateSha256"]
    report = {
        "schemaVersion": 1,
        "experiment": "E2-PostgreSQL-Real-40P01-Atomic-Retry",
        "status": "PASS",
        "classification": "SYNTHETIC_OPT_IN_SQL_DEADLOCK_SINGLE_HOST_NOT_CAPACITY",
        "fixture": {
            "flag": "E2_ENABLE_DEADLOCK_FIXTURE=1",
            "operationIds": ["e2-deadlock-a", "e2-deadlock-b"],
            "sourceTargetPairs": [[1, 2], [2, 1]],
            "amountCents": 41,
            "firstAttemptUnorderedOnly": True,
            "orderedOnRetry": True
        },
        "results": results,
        "sourceSha256": {
            str(p.relative_to(LAB)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                HERE / "test_deadlock.py",
                HERE / "OrleansLab/PgDurableLedger.cs",
                HERE / "OrleansLab/Program.cs",
                LAB / "e1_pg/oracle.py"
            )
        },
        "limitations": (
            "Real 40P01 under controlled, deliberately unordered first-attempt "
            "row locking in a disposable single-host test; not evidence of "
            "natural production deadlock frequency, cross-silo failover, "
            "physical scaling, mainframe throughput or MIPS equivalence."
        )
    }
    (OUT / "e2-deadlock.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
