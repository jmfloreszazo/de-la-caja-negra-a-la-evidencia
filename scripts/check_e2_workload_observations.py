#!/usr/bin/env python3
"""Fail-closed, reproducible validation of original E2 hot-key CI observation.

The 6-case source hashes are pinned to the historic CI run, not falsely
compared to subsequently modified code. Full raw data remains in Actions.
This is NOT a production workload or proven Orleans scaling advantage.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
record = json.loads(
    (ROOT / "evidence/runs/e2-orleans-workload-summary.json").read_text("utf-8")
)
data = record["observation"]
assert record["schemaVersion"] == 1
assert record["experiment"] == data["experiment"] == "E2-Orleans-Synthetic-Load-1000"
assert record["runId"] == 41055928136
assert record["jobId"] == 124063312118
assert record["artifactId"] == 12977285976
assert record["sourceCommit"] == "4bd9e4da6ac1d8f6609813dfbd81da96c23946e0"
assert record["checkoutCommit"] == "0481c700d7cabd359a37288734209b6469e89d79"
assert record["sourceCommit"] != record["checkoutCommit"]
assert re.fullmatch("[0-9a-f]{40}", record["checkoutCommit"])
assert record["url"].endswith("/41055928136")
assert record["artifactUrl"].endswith("/artifacts/12977285976")
assert record["classification"] == "EXECUTED_SYNTHETIC_SINGLE_SILO_FIXED_WORKLOAD_NOT_CAPACITY"
assert data["status"] == "PASS"
assert data["controls"] == {
    "deterministicIdenticalOfferedCommands": "PASS",
    "sixMatchedRouteAndProfileRuns": "PASS",
    "sixHundredDurableCommittedTransfers": "PASS",
    "sevenIndependentLedgerInvariantsPerRun": "PASS",
    "identicalPersistedStateByRoutePerProfile": "PASS",
}
rows = data["workloadRuns"]
assert len(rows) == 6
assert sum(row["committed"] for row in rows) == 600
assert sum(row["offeredRequests"] for row in rows) == 600
profiles = ("uniform", "five_percent_hot", "one_account_half_intents")
for i, profile in enumerate(profiles):
    direct, grain = rows[2*i:2*i+2]
    assert direct["profile"] == grain["profile"] == profile
    assert direct["route"] == "direct" and grain["route"] == "orleans"
    assert direct["stateSha256"] == grain["stateSha256"]
    assert re.fullmatch("[a-f0-9]{64}", direct["stateSha256"])
    for row in (direct, grain):
        assert row["committed"] == row["offeredRequests"] == 100
        assert row["retries"] == 0
        assert row["committedPerProcessWallSecond"] > 0
        timings = row["clientObservedRequestLatencyMs"]
        assert 0 <= timings["p50"] <= timings["p95"] <= timings["p99"] <= timings["max"]
assert data["sourceSha256"] == {
    "e2_orleans/test_workloads.py": "745061b5cb7b4c3596d3123708eb362734a5b1c22de67ccf5a75c4c433d41959",
    "e2_orleans/oracle_workload.py": "1c5caa71e955674b31f4853b61fc1f84f747602b50528bc9478601fe630c3038",
    "e2_orleans/OrleansLab/Program.cs": "f3ceda87c3ee0bf7cb3d31e6d5c0c0054a25d4f7321524a691ea3986350a87c1",
    "e2_orleans/OrleansLab/Contracts.cs": "9e455c56e007f485a2ae6f71b9c56bf0c39753527a09be409045ade68bad28e1",
    "e2_orleans/OrleansLab/PgDurableLedger.cs": "f6c8f6cbfd26c56b300a0249ca7d2da80984ccb41506779ba08ea0f703e5c884",
}
print("E2 WORKLOAD: PASS — three seeded profiles, six original runs, "
      "600 commits, matching state digests, raw CI artifact retained; "
      "single silo, not a throughput or multi-node capacity qualification")
