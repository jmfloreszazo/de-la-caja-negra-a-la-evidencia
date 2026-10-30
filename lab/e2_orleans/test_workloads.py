#!/usr/bin/env python3
"""E2-B01/B02/B03 fixed synthetic load: direct ledger vs Orleans grain.

Single local silo, 1,000 disposable accounts, exactly 50 hot accounts.
Uses identical operation IDs, accounts, amounts, offers and SQL pool across
both routes. Never equate these results with production, scale or MIPS.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
RESULT = LAB / "results/e2"
RESULT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(LAB / "e1_pg"))
from ledger import connect, reset
from oracle_workload import verify, EXPECTED_TOTAL

APP = HERE / "OrleansLab/bin/Release/net10.0/OrleansLab.dll"
WORKLOAD_SEED = 20261030
ACCOUNT_COUNT = 1000
HOT_ACCOUNT_COUNT = 50
COMMAND_COUNT = 100
ARRIVAL_SPACING_MS = 3
PROFILES = ("uniform", "five_percent_hot", "one_account_half_intents")
ROUTES = ("direct", "orleans")
EXPECTED_KEYS = {
    "nonnegative", "conserved", "balancedPostings",
    "twoPostingsPerCommit", "noPostingsForRejection",
    "outboxAtomic", "projectionAgrees"
}


def fixture():
    reset()
    with connect() as db:
        db.execute("INSERT INTO accounts(id,balance) "
                   "SELECT n,100000 FROM generate_series(17,1000) n")
        assert db.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 1000
        assert db.execute("SELECT SUM(balance) FROM accounts").fetchone()[0] == EXPECTED_TOTAL
    assert all(verify().values())


def commands(profile):
    rng = random.Random(WORKLOAD_SEED + PROFILES.index(profile))
    source_list = []
    for i in range(COMMAND_COUNT):
        if profile == "uniform":
            src = rng.randint(1, ACCOUNT_COUNT)
        elif profile == "five_percent_hot":
            # 80% of attempted operations originate in exactly 50 / 1000
            # hot account IDs. It is not an 80%-of-accounts skew.
            src = rng.randint(1, 50) if i < 80 else rng.randint(51, 1000)
        else:
            # Precisely 50% of requests are sourced from account 1.
            src = 1 if i < 50 else rng.randint(2, 1000)
        source_list.append(src)

    rng.shuffle(source_list)
    result = []
    for i, src in enumerate(source_list):
        dst = rng.randint(1, ACCOUNT_COUNT - 1)
        if dst >= src:
            dst += 1
        result.append({
            "operationId": f"e2-{profile.replace('_', '-')}-{i:03}",
            "sourceAccountId": src,
            "targetAccountId": dst,
            "amountCents": 1,
            "fault": "none",
            "arrivalOffsetMs": ARRIVAL_SPACING_MS * i
        })
    assert len(result) == 100 and all(
        1 <= x["sourceAccountId"] <= 1000 and
        x["sourceAccountId"] != x["targetAccountId"] for x in result
    )
    if profile == "five_percent_hot":
        assert sum(x["sourceAccountId"] <= 50 for x in result) == 80
    if profile == "one_account_half_intents":
        assert sum(x["sourceAccountId"] == 1 for x in result) == 50
    return result


def snapshot():
    with connect() as db:
        result = {
            "accounts": db.execute(
                "SELECT id,balance FROM accounts ORDER BY id").fetchall(),
            "operations": db.execute(
                "SELECT id,src,dst,amount,status FROM operations ORDER BY id").fetchall(),
            "postings": db.execute(
                "SELECT op,account,delta FROM postings ORDER BY op,account").fetchall(),
            "outbox": db.execute(
                "SELECT op,event FROM outbox ORDER BY op").fetchall()
        }
    return result


def percentile(values, p):
    ordered = sorted(values)
    rank = (len(ordered) - 1) * p / 100
    lower, upper = math.floor(rank), math.ceil(rank)
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower), 3)


def execute(profile, route, workload):
    fixture()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix="e2-benchmark-",
        encoding="utf-8", dir=RESULT, delete=False
    ) as fd:
        json.dump({"route": route, "concurrent": True, "commands": workload}, fd)
        filename = Path(fd.name)
    started = time.perf_counter()
    try:
        process = subprocess.run(
            ["dotnet", str(APP), "run", str(filename)],
            capture_output=True, text=True, timeout=180,
            env={**os.environ, "E2_MAX_ACCOUNT_ID": "1000"}
        )
    finally:
        filename.unlink(missing_ok=True)
    elapsed = time.perf_counter() - started
    assert process.returncode == 0, (
        "Orleans workload process failed", profile, route,
        process.returncode, process.stderr[-1800:])
    data = json.loads(process.stdout)
    assert data["route"] == route and data["concurrent"] is True
    assert data["sourceOfTruth"] == "postgresql-transaction"
    statuses = [x["status"] for x in data["results"]]
    assert len(statuses) == COMMAND_COUNT
    assert statuses == ["COMMITTED"] * COMMAND_COUNT, {
        "profile": profile, "route": route, "statuses": statuses
    }
    timing = data["timing"]
    assert len(timing) == COMMAND_COUNT
    latency = [float(x["elapsedMs"]) for x in timing]
    assert all(v >= 0 for v in latency)
    assert len(data["results"]) == len(timing)
    assert all(
        x["handledBy"].startswith("grain-") if route == "orleans"
        else x["handledBy"] == "direct-ledger"
        for x in data["results"]
    )
    actual = snapshot()
    assert len(actual["accounts"]) == ACCOUNT_COUNT
    assert len(actual["operations"]) == COMMAND_COUNT
    assert len(actual["postings"]) == COMMAND_COUNT * 2
    assert len(actual["outbox"]) == COMMAND_COUNT
    oracles = verify()
    assert set(oracles) == EXPECTED_KEYS and all(oracles.values()), oracles
    return {
        "profile": profile, "route": route, "offeredRequests": COMMAND_COUNT,
        "committed": COMMAND_COUNT, "rejected": 0,
        "retries": sum(int(x["retries"]) for x in data["results"]),
        "retrySqlStates": [x["retrySqlStates"] for x in data["results"]],
        "totalProcessElapsedSeconds": round(elapsed, 3),
        "committedPerProcessWallSecond": round(COMMAND_COUNT / elapsed, 3),
        "clientObservedRequestLatencyMs": {
            "p50": percentile(latency, 50),
            "p95": percentile(latency, 95),
            "p99": percentile(latency, 99),
            "max": round(max(latency), 3)
        },
        "dispatchLatenessMs": {
            "p95": percentile([
                max(0, t["dispatchedAtMs"] - c["arrivalOffsetMs"])
                for t, c in zip(timing, workload)
            ], 95)
        },
        "oracle": oracles,
        "state": actual
    }


def main():
    assert APP.is_file(), "Build OrleansLab .NET 10 before running workload"
    observations = []
    for profile in PROFILES:
        commands_for_profile = commands(profile)
        results = [execute(profile, route, commands_for_profile) for route in ROUTES]
        assert results[0]["state"] == results[1]["state"], (
            "Direct versus Orleans persisted ledger mismatch", profile
        )
        digest = hashlib.sha256(json.dumps(
            results[0]["state"], separators=(",", ":"),
            ensure_ascii=True).encode("utf-8")).hexdigest()
        for result in results:
            result.pop("state")
            result["stateSha256"] = digest
            observations.append(result)

    manifest = {
        "schemaVersion": 1,
        "experiment": "E2-Orleans-Synthetic-Load-1000",
        "status": "PASS",
        "classification": "SYNTHETIC_SINGLE_SILO_FIXED_WORKLOAD_NOT_CAPACITY",
        "seed": WORKLOAD_SEED, "accountCount": ACCOUNT_COUNT,
        "hotAccountCount": HOT_ACCOUNT_COUNT,
        "profiles": list(PROFILES),
        "routes": list(ROUTES),
        "commandsPerProfilePerRoute": COMMAND_COUNT,
        "arrivalSpacingMs": ARRIVAL_SPACING_MS,
        "profileDefinitions": {
            "uniform": "100 uniform seeded source accounts from IDs 1..1000",
            "five_percent_hot": "Exactly 50 of 1000 accounts qualify as hot; 80 of 100 intents source IDs 1..50",
            "one_account_half_intents": "Exactly 50 of 100 intents source account ID 1"
        },
        "controls": {
            "deterministicIdenticalOfferedCommands": "PASS",
            "sixMatchedRouteAndProfileRuns": "PASS",
            "sixHundredDurableCommittedTransfers": "PASS",
            "sevenIndependentLedgerInvariantsPerRun": "PASS",
            "identicalPersistedStateByRoutePerProfile": "PASS"
        },
        "runs": observations,
        "sourceSha256": {
            str(p.relative_to(LAB)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                HERE / "test_workloads.py",
                HERE / "oracle_workload.py",
                HERE / "OrleansLab/Program.cs",
                HERE / "OrleansLab/Contracts.cs",
                HERE / "OrleansLab/PgDurableLedger.cs"
            )
        },
        "limits": (
            "Three seeded closed-host open-loop-style arrival schedules, not "
            "a capacity ceiling. Client and Orleans host share one process; "
            "no independent client machine, prolonged warm-up, distributed "
            "Orleans cluster, failure injection, coordinated-omission proof "
            "or mainframe performance equivalence."
        )
    }
    (RESULT / "e2-workloads.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": manifest["status"],
        "experiment": manifest["experiment"],
        "controls": manifest["controls"],
        "workloadRuns": [{
            k: v for k, v in row.items()
            if k in ("route", "profile", "offeredRequests", "committed",
                     "retries", "clientObservedRequestLatencyMs",
                     "committedPerProcessWallSecond", "stateSha256")
        } for row in observations],
        "sourceSha256": manifest["sourceSha256"]
    }, indent=2))


if __name__ == "__main__":
    main()
