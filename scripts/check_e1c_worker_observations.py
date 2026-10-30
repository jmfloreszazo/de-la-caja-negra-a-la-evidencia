#!/usr/bin/env python3
"""Verify the archived E1c SQL Server worker-matrix execution, fail closed.

This validates the immutable historical source manifest of one CI execution;
the latest persistent-worker source is validated by the companion E1c checker.
Neither is a production or mainframe performance benchmark.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
record = json.loads((ROOT / "evidence/runs/e1c-sqlserver-worker-parity.json").read_text(encoding="utf-8"))
data = record["observation"]

assert record["schemaVersion"] == data["schemaVersion"] == 1
assert record["experiment"] == data["experiment"] == "E1c-SQLServer-Worker-Parity"
assert record["runId"] == 41042317263
assert record["jobId"] == 124017850214
assert record["artifactId"] == 12970982648
assert record["sourceCommit"] == "9e9f5787aa99302acb86b1251d7657cb82f9513b"
assert re.fullmatch(r"[0-9a-f]{40}", record["checkoutCommit"])
assert record["checkoutCommit"] != record["sourceCommit"]
assert record["url"].endswith("/" + str(record["runId"]))
assert record["classification"] == "EXECUTED_SYNTHETIC_ACCOUNTING_WORKLOAD_NOT_CAPACITY"
assert data["classification"] == "SYNTHETIC_ACCOUNTING_WORKLOAD_NOT_CAPACITY"
assert data["status"] == "PASS"

assert data["controls"] == {
    "eightUniformHotWorkerCases": "PASS",
    "bothCandidatesCommitAll960": "PASS",
    "completeFourTableParity": "PASS",
    "sevenIndependentOracleInvariants": "PASS",
}
assert data["workerCounts"] == [1, 2, 4, 8]
assert data["patterns"] == ["uniform", "hot"]
assert data["operationsPerWorker"] == 32
assert data["totalLogicalOperations"] == 960
assert len(data["cases"]) == 8
assert sum(c["operations"] for c in data["cases"]) == 960
expected_invariants = {
    "nonnegative", "conserved", "balancedPostings",
    "twoPostingsPerCommit", "noPostingsForRejection",
    "outboxAtomic", "projectionAgrees",
}
for i, case in enumerate(data["cases"]):
    pattern = ("uniform", "hot")[i // 4]
    workers = (1, 2, 4, 8)[i % 4]
    count = workers * 32
    assert case["pattern"] == pattern and case["workers"] == workers
    assert case["operationsPerWorker"] == 32
    assert case["operations"] == case["referenceCommitted"] == (
        case["sqlServerCommitted"]
    ) == count
    assert case["persistedParity"] is True
    assert case["accounts"] == 16
    assert case["operationsPersisted"] == count
    assert case["postings"] == count * 2
    assert case["outbox"] == count
    assert set(case["oracle"]) == expected_invariants
    assert all(value is True for value in case["oracle"].values())

assert data["environment"]["sqlServerVersion"].startswith("16.")
assert data["environment"]["dotnetSdk"].startswith("10.")
# The 41042317263 observation was produced before the persistent-worker
# source change. Its original source manifest is immutable and must match
# the recorded hashes, NOT the latest working-tree files. Current source
# hashes are checked separately against the subsequent 41043087791
# persistent-worker run in scripts/check_e1c_observations.py.
EXPECTED_HISTORICAL_SOURCE_SHA256 = {
    "Bank/Program.cs": "72e6ff2bf59fd8889158b2488e3b8a5eb6f67b8e05cab27dc2336b74b6ad8253",
    "bank_test.py": "4e633c890889bf7a6db48f0dfc9b1f6d1cb16c75a5795c6d497eb1c7545f6ca5",
    "e1_sqlserver/SqlBank/Program.cs": "2af2bd31c70e5031dfe8ae9ba2c82b0e441214cfb156d329519b6c2b7a81a4cb",
    "e1_sqlserver/SqlOracle/Program.cs": "687fd9d50c44012ae608b9437e3bfa501fc9e3364ccd20a9b9d091cb669a0324",
    "e1_sqlserver/test_e1c.py": "d3e62b4f96f9599d2deaa9c9e11bf5ae9c44fee06f772eb4898c1ec356c13e9b",
    "e1_sqlserver/test_worker_parity.py": "f12230bb8680c56ce925344eea2cf1eac015f2847c255bfad8519ab145ca7f44",
}
assert data["sourceSha256"] == EXPECTED_HISTORICAL_SOURCE_SHA256
assert len(EXPECTED_HISTORICAL_SOURCE_SHA256) == 6

print("E1C SQL SERVER WORKER MATRIX: PASS; eight cases, 960 matching "
      "transfers per engine, seven independent invariants per case. "
      "Not a throughput or mainframe equivalence claim.")
