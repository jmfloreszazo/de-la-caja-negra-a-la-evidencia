#!/usr/bin/env python3
"""Fail-closed validator for original E2 single-silo functional CI evidence.

An immutable historical run must not be rewritten or made to match newer
source files. The E2 overall benchmark and distributed faults remain open.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
record = json.loads((ROOT / "evidence/runs/e2-orleans-smoke.json").read_text("utf-8"))
data = record["observation"]
assert record["schemaVersion"] == data["schemaVersion"] == 1
assert record["experiment"] == data["experiment"] == "E2-Orleans-Persistent-Ledger-Smoke"
assert record["runId"] == 41053628769 and record["jobId"] == 124055556076
assert record["artifactId"] == 12975297794
assert record["sourceCommit"] == "8eac88f835451e42e9adeb997c933aa4ac41427c"
assert record["checkoutCommit"] == "5f438d7a5595971c477a8530ff76dcc12d3e6214"
assert re.fullmatch(r"[0-9a-f]{40}", record["sourceCommit"])
assert record["checkoutCommit"] != record["sourceCommit"]
assert record["url"].endswith("/41053628769")
assert record["classification"] == "EXECUTED_SYNTHETIC_SINGLE_SILO_FUNCTIONAL_NOT_CAPACITY"
assert data["classification"] == "SYNTHETIC_SINGLE_SILO_FUNCTIONAL_NOT_CAPACITY"
assert data["status"] == "PASS" and len(data["controls"]) == 5
assert all(v == "PASS" for v in data["controls"].values())
expected_status = [
    "COMMITTED", "DUPLICATE_COMMITTED", "ID_CONFLICT", "REJECTED",
    "DUPLICATE_REJECTED", "ID_CONFLICT", "INVALID", "INVALID",
    "INVALID", "INVALID", "INJECTED_ROLLBACK", "AMBIGUOUS_RESPONSE",
    "DUPLICATE_COMMITTED", "COMMITTED", "COMMITTED"
]
assert len(data["functional"]) == 2
assert {row["route"] for row in data["functional"]} == {"direct", "orleans"}
expected_invariants = {
    "nonnegative", "conserved", "balancedPostings",
    "twoPostingsPerCommit", "noPostingsForRejection",
    "outboxAtomic", "projectionAgrees",
}
for row in data["functional"]:
    assert row["cases"] == 15
    assert row["statuses"] == expected_status
    assert row["persistedStateMatchesProtectedSQLite"] is True
    assert set(row["independentOracle"]) == expected_invariants
    assert all(row["independentOracle"].values())
assert len(data["concurrent"]) == 2
for row in data["concurrent"]:
    assert row["overdraftStatuses"] == ["COMMITTED", "REJECTED"]
    assert row["duplicateStatuses"] == [
        "COMMITTED", "DUPLICATE_COMMITTED",
        "DUPLICATE_COMMITTED", "DUPLICATE_COMMITTED"
    ]
    assert (row["committed"], row["postings"], row["outbox"]) == (2, 4, 2)
    assert set(row["independentOracle"]) == expected_invariants
    assert all(row["independentOracle"].values())
negative = data["oracleNegative"]
assert set(negative["before"]) == set(negative["corrupted"]) == (
    set(negative["restored"])
) == expected_invariants
assert all(negative["before"].values())
assert negative["restored"] == negative["before"]
assert {key for key, value in negative["corrupted"].items() if value is False} == {
    "balancedPostings", "twoPostingsPerCommit", "projectionAgrees"
}
expected_hashes = {
    "Bank/Program.cs": "72e6ff2bf59fd8889158b2488e3b8a5eb6f67b8e05cab27dc2336b74b6ad8253",
    "e1_pg/PgBank/Program.cs": "eb61acea9673cf14e999adf2c01a03df418c385dee0e3e1f6d777bbca53f5f32",
    "e2_orleans/OrleansLab/OrleansLab.csproj": "c1cc127ea0fa9f4527bc37c6a6a19dd36f3f5a7916a197e207760d37a6c58fa5",
    "e2_orleans/OrleansLab/Program.cs": "5505c066b7f9bdda38848087d1f5e9bd770616ae0fe419a287b4910876269e35",
    "e2_orleans/OrleansLab/Contracts.cs": "de4eb9d23da4ec213a54fd52e3ea48c9de43bb6fc2d86aaa5ecc4b5a9c917ebb",
    "e2_orleans/OrleansLab/PgDurableLedger.cs": "b86d2ca9425b2c15349ea32a728d3f0b695b6c6943e6c6d7b4f38fed677950a2",
    "e2_orleans/test_e2.py": "ee9718ca72b245955a1e1677028e90502610ec645a4bd1201bf4f2852b223eb5",
}
assert data["sourceSha256"] == expected_hashes
print("E2-SMOKE EVIDENCE: PASS — five synthetic controls, 15 cases per route, "
      "two concurrency profiles, full negative oracle, original source hashes")
