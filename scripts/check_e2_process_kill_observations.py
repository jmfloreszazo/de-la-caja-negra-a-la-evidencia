#!/usr/bin/env python3
"""Fail closed on the original E2 single-host SIGKILL recovery observation.

Keep immutable historical source SHA-256 values, original run/job/artifact
and independent accounting invariants. Never claim distributed failover.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
record = json.loads((ROOT / "evidence/runs/e2-orleans-process-kill.json").read_text("utf-8"))
data = record["observation"]
assert record["schemaVersion"] == data["schemaVersion"] == 1
assert record["experiment"] == data["experiment"] == "E2-Orleans-Actual-Cohost-Process-Kill"
assert record["runId"] == 41056976342
assert record["jobId"] == 124066860297
assert record["artifactId"] == 12976807635
assert record["sourceCommit"] == "63b062f18b5eb8dc427d807c49019a4657215f07"
assert record["checkoutCommit"] == "3c977fde07deff122ac3b0a4db5f042a790ec0e0"
assert re.fullmatch(r"[a-f0-9]{40}", record["sourceCommit"])
assert record["sourceCommit"] != record["checkoutCommit"]
assert record["url"].endswith("/41056976342")
assert record["artifactUrl"].endswith("/artifacts/12976807635")
assert record["classification"] == "EXECUTED_SINGLE_COHOST_PROCESS_KILL_NOT_MULTISILO"
assert data["classification"] == "SYNTHETIC_SINGLE_COHOST_SIGKILL_NOT_MULTISILO_FAILOVER"
assert data["status"] == "PASS"
assert data["controls"] == {
    "actualProcessSIGKILLBeforeAndAfterCommit": "PASS",
    "rollbackOnDatabaseSessionDeath": "PASS",
    "postCommitAmbiguityResolvesByOperationId": "PASS",
    "exactlyOneDurablePostingAndOutbox": "PASS",
    "isolatedNonAtomicSplitRejectedByIndependentOracle": "PASS",
}
runs = data["killedRuns"]
assert len(runs) == 4
expected_invariants = {
    "nonnegative", "conserved", "balancedPostings",
    "twoPostingsPerCommit", "noPostingsForRejection",
    "outboxAtomic", "projectionAgrees",
}
for route in ("direct", "orleans"):
    for fault, expected, recovery in (
        ("kill-before-commit",
         {"operations": 0, "postings": 0, "outbox": 0}, "COMMITTED"),
        ("kill-after-commit",
         {"operations": 1, "postings": 2, "outbox": 1}, "DUPLICATE_COMMITTED")
    ):
        entry = next(row for row in runs
                     if row["route"] == route and row["fault"] == fault)
        assert entry["exitCode"] == -9
        assert entry["afterKill"] == expected
        assert entry["recoveryStatus"] == recovery
        assert entry["finalExactlyOneDurableEffect"] is True
        assert set(entry["independentOracle"]) == expected_invariants
        assert all(entry["independentOracle"].values())
negative = data["negativeSplit"]
assert set(negative["before"]) == expected_invariants
assert all(negative["before"].values())
assert negative["restored"] == negative["before"]
assert {k for k, v in negative["unsafeSplit"].items() if v is False} == {
    "conserved", "projectionAgrees"
}
assert data["sourceSha256"] == {
    "e2_orleans/test_process_crash.py": "69703e3f053e875f9502b65edab5d8afa889c852d2c12e41ec2a14349f187b73",
    "e2_orleans/OrleansLab/PgDurableLedger.cs": "ac6f779113c5c6efd48c28461fc4c8696218fa63da1409f5de69cb99d7b17f72",
    "e2_orleans/OrleansLab/Program.cs": "f3ceda87c3ee0bf7cb3d31e6d5c0c0054a25d4f7321524a691ea3986350a87c1",
    "e2_orleans/OrleansLab/Contracts.cs": "9e455c56e007f485a2ae6f71b9c56bf0c39753527a09be409045ade68bad28e1",
    "e1_pg/oracle.py": "3f2874842e9febcc84584bf4a266920028840ccac9d404f75cb9f4363fb4fc09",
}
print("E2 PROCESS KILL: PASS (4 actual SIGKILL, two phases on two routes, "
      "independent oracle rejects partial SQL split, persisted exactly once). "
      "No multi-silo failover or mainframe capacity claim.")
