#!/usr/bin/env python3
"""Verify the archived E1c SQL Server worker-matrix execution, fail closed.

This is a check of one completed CI observation and its exact current source
bytes, NOT a benchmark or proof of production/mainframe capacity.
"""
import hashlib
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
assert len(data["sourceSha256"]) == 6
for rel, expected in data["sourceSha256"].items():
    source = ROOT / "lab" / rel
    assert source.is_file(), rel
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    assert actual == expected, (rel, expected, actual)

print("E1C SQL SERVER WORKER MATRIX: PASS; eight cases, 960 matching "
      "transfers per engine, seven independent invariants per case. "
      "Not a throughput or mainframe equivalence claim.")
