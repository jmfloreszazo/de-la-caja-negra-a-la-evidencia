#!/usr/bin/env python3
"""Fail closed unless the original E1c SQL Server CI result is internally sound.

Checks original run/job/artifact IDs, source SHA-256, all synthetic outcomes,
actual 1205/1222 retries, isolated accounting-oracle negative controls and
the deliberately unsafe SNAPSHOT anomaly. Not a production-capacity proof.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
record = json.loads((ROOT/"evidence/runs/e1c-sqlserver-initial.json")
                    .read_text(encoding="utf-8"))
data = record["observation"]
assert record["schemaVersion"] == data["schemaVersion"] == 1
assert record["experiment"] == data["experiment"] == "E1c-SQL-Server-2022"
assert record["runId"] == 41040632819
assert record["jobId"] == 124012249407
assert record["artifactId"] == 12970201805
assert record["sourceCommit"] == "4e1d79b597f8c393cdc349e92c604fcc0aecc9c4"
assert re.fullmatch(r"[0-9a-f]{40}", record["checkoutCommit"])
assert record["url"].endswith("/"+str(record["runId"]))
assert record["classification"] == data["classification"] == (
    "EXECUTED_SYNTHETIC_SQLSERVER_NOT_MAINFRAME"
)
assert data["status"] == "PASS"
expected_controls = {
    "sequentialCrossEngineParity", "overdraftAndIdempotencyUnderConcurrency",
    "lockReleasedDuringRetry", "boundedLockTimeoutAndRecovery",
    "independentOracleRejectsCorruption", "deadlock1205WholeTransactionRetry",
    "snapshotWriteSkewAndSerializableDefense", "boundedSqlClientPool"
}
assert set(data["controls"]) == expected_controls
assert all(value == "PASS" for value in data["controls"].values())
assert len(data["sequentialCases"]) == 16
for case in data["sequentialCases"]:
    assert case["persistedParity"] is True, case["name"]
    assert case["counts"]["accounts"] == 16
    assert len(case["oracle"]) == 7 and all(case["oracle"].values())

observations = data["observations"]
deadlock = observations["deadlock"]
assert len(deadlock) == 2
assert all(row["status"] == "COMMITTED" for row in deadlock)
assert any(1205 in row["retrySqlErrors"] for row in deadlock)
isolation = observations["isolation"]
assert isolation["snapshot"]["remainingActive"] == 0
assert isolation["serializable"]["remainingActive"] >= 1
assert any(1205 in row["retrySqlErrors"] for row in
           isolation["serializable"]["results"])
faults = observations["faults"]
assert 1222 in faults["lockReleased"]["retrySqlErrors"]
assert faults["lockReleased"]["status"] == "COMMITTED"
assert faults["lockExhaustion"]["status"] == "RETRY_EXHAUSTED"
assert faults["lockExhaustion"]["retrySqlErrors"] == [1222] * 6
before = faults["oracleVectors"]["before"]
corrupted = faults["oracleVectors"]["corrupted"]
restored = faults["oracleVectors"]["restored"]
assert len(before) == len(corrupted) == len(restored) == 7
assert all(before.values()) and before == restored
assert {key for key, value in corrupted.items() if value is False} == {
    "balancedPostings", "twoPostingsPerCommit", "projectionAgrees"
}
assert data["environment"]["sqlServerVersion"].startswith("16.")
assert data["environment"]["dotnetSdk"].startswith("10.")
assert data["sourceSha256"] == {
    "e1_sqlserver/schema.sql": "afca447dc6c6a420e71062444d25788e9c93390c6b4e689b915716370e405342",
    "e1_sqlserver/SqlBank/Program.cs": "2af2bd31c70e5031dfe8ae9ba2c82b0e441214cfb156d329519b6c2b7a81a4cb",
    "e1_sqlserver/SqlBank/SqlBank.csproj": "cf105657f99f01fddc92e6864807f500432777786525310fef2f98a8b285b61a",
    "e1_sqlserver/SqlOracle/Program.cs": "687fd9d50c44012ae608b9437e3bfa501fc9e3364ccd20a9b9d091cb669a0324",
    "e1_sqlserver/SqlFixtures/Program.cs": "8ae86793ce6e285cb1101a8f04f585b737749b38761bcaf1430243b73e1fe311",
    "e1_sqlserver/test_e1c.py": "ac478128cd52784fc6217c10f8776c1f8b6a888ce80c5080f76b84e1cef2707c",
    "Bank/Program.cs": "72e6ff2bf59fd8889158b2488e3b8a5eb6f67b8e05cab27dc2336b74b6ad8253"
}
# The original run is an immutable historical execution, not the current
# source tree after subsequent E1c test extensions. Compare current file
# hashes in a separate extended snapshot, never rewrite the old run.
print("E1C OBSERVATION: PASS (16 parity cases, 8 controls, "
      "1205 deadlock, 1222 bounded retries, SNAPSHOT negative, "
      "SERIALIZABLE defense, independent seven-invariant oracle)")
