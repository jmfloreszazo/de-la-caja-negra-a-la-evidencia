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
# E1c extended run is a distinct execution, never a rewrite of the
# earlier eight-control source snapshot.
extended = json.loads((ROOT/"evidence/runs/e1c-sqlserver-extended.json")
                      .read_text(encoding="utf-8"))
new_data = extended["observation"]
assert extended["schemaVersion"] == new_data["schemaVersion"] == 1
assert extended["experiment"] == new_data["experiment"] == "E1c-SQL-Server-2022"
assert extended["runId"] == 41041573996
assert extended["jobId"] == 124015395657
assert extended["artifactId"] == 12970641379
assert extended["sourceCommit"] == "8c3024349dd5c63c9b50fd0b9d41876f3bcddf2e"
assert re.fullmatch(r"[0-9a-f]{40}", extended["checkoutCommit"])
assert extended["url"].endswith("/"+str(extended["runId"]))
assert extended["classification"] == new_data["classification"] == (
    "EXECUTED_SYNTHETIC_SQLSERVER_NOT_MAINFRAME"
)
assert new_data["status"] == "PASS"
assert set(new_data["controls"]) == expected_controls | {
    "databaseUniqueKeyConstraint", "boundedSqlClientCommandTimeout"
}
assert all(v == "PASS" for v in new_data["controls"].values())
assert len(new_data["sequentialCases"]) == 16
assert all(c["persistedParity"] and len(c["oracle"]) == 7 and
           all(c["oracle"].values()) for c in new_data["sequentialCases"])
assert any(1205 in x["retrySqlErrors"] for x in new_data["observations"]["deadlock"])
assert new_data["observations"]["faults"]["lockExhaustion"]["retrySqlErrors"] == [1222]*6
assert new_data["observations"]["isolation"]["snapshot"]["remainingActive"] == 0
assert new_data["observations"]["isolation"]["serializable"]["remainingActive"] >= 1
assert new_data["sourceSha256"] == {
    "e1_sqlserver/schema.sql": "afca447dc6c6a420e71062444d25788e9c93390c6b4e689b915716370e405342",
    "e1_sqlserver/SqlBank/Program.cs": "2af2bd31c70e5031dfe8ae9ba2c82b0e441214cfb156d329519b6c2b7a81a4cb",
    "e1_sqlserver/SqlBank/SqlBank.csproj": "cf105657f99f01fddc92e6864807f500432777786525310fef2f98a8b285b61a",
    "e1_sqlserver/SqlOracle/Program.cs": "687fd9d50c44012ae608b9437e3bfa501fc9e3364ccd20a9b9d091cb669a0324",
    "e1_sqlserver/SqlFixtures/Program.cs": "ffb5b3df77c30d390f8f231ea61ca1be22229d0d2a40b21b2537533455e7796a",
    "e1_sqlserver/test_e1c.py": "d3e62b4f96f9599d2deaa9c9e11bf5ae9c44fee06f772eb4898c1ec356c13e9b",
    "Bank/Program.cs": "72e6ff2bf59fd8889158b2488e3b8a5eb6f67b8e05cab27dc2336b74b6ad8253"
}
# This 10-control run has its own fixed historical source manifest. The
# subsequent 960-transfer worker implementation must be checked separately.
print("E1C EXTENDED OBSERVATION: PASS (10 controls including SQL unique key "
      "and SqlClient command timeout; historical manifest pinned)")


# Independently preserve both real 960-transfer runs. The earlier run
# launched per-transfer CLI processes; the newer run used persistent
# .NET worker processes on both the SQLite and SQL Server sides.
WORKER_RUNS = (
    ("e1c-sqlserver-worker-parity.json", 41042317263, 124017850214,
     12970982648, "9e9f5787aa99302acb86b1251d7657cb82f9513b",
     "EXECUTED_SYNTHETIC_ACCOUNTING_WORKLOAD_NOT_CAPACITY",
     {
    "Bank/Program.cs": "72e6ff2bf59fd8889158b2488e3b8a5eb6f67b8e05cab27dc2336b74b6ad8253",
    "bank_test.py": "4e633c890889bf7a6db48f0dfc9b1f6d1cb16c75a5795c6d497eb1c7545f6ca5",
    "e1_sqlserver/SqlBank/Program.cs": "2af2bd31c70e5031dfe8ae9ba2c82b0e441214cfb156d329519b6c2b7a81a4cb",
    "e1_sqlserver/SqlOracle/Program.cs": "687fd9d50c44012ae608b9437e3bfa501fc9e3364ccd20a9b9d091cb669a0324",
    "e1_sqlserver/test_e1c.py": "d3e62b4f96f9599d2deaa9c9e11bf5ae9c44fee06f772eb4898c1ec356c13e9b",
    "e1_sqlserver/test_worker_parity.py": "f12230bb8680c56ce925344eea2cf1eac015f2847c255bfad8519ab145ca7f44"
}),
    ("e1c-sqlserver-worker-parity-persistent.json", 41043087791,
     124020405785, 12971391392, "7694e5c306d6c40dc76955b0a25b55382a023ae5",
     "EXECUTED_SYNTHETIC_SQLSERVER_ACCOUNTING_WORKLOAD_NOT_CAPACITY",
     {
    "Bank/Program.cs": "72e6ff2bf59fd8889158b2488e3b8a5eb6f67b8e05cab27dc2336b74b6ad8253",
    "bank_test.py": "4e633c890889bf7a6db48f0dfc9b1f6d1cb16c75a5795c6d497eb1c7545f6ca5",
    "e1_sqlserver/SqlBank/Program.cs": "2324fcf3bb7745804585fe690c1d7fcd4e30e7f3e545c3c118c60205d4f97188",
    "e1_sqlserver/SqlOracle/Program.cs": "687fd9d50c44012ae608b9437e3bfa501fc9e3364ccd20a9b9d091cb669a0324",
    "e1_sqlserver/test_e1c.py": "29c2d956a63d24e39c73171d4ac097f5e622262b0482e70cf841b5c4bd26b082",
    "e1_sqlserver/test_worker_parity.py": "ac78922d4786150731e72640594a4be4ddff6806b9741ba6f4370e29ffc0a059"
}),
)
for filename, run_id, job_id, artifact_id, source_sha, kind, hashes in WORKER_RUNS:
    snapshot = json.loads((ROOT/"evidence/runs"/filename).read_text(encoding="utf-8"))
    observed = snapshot["observation"]
    assert snapshot["schemaVersion"] == observed["schemaVersion"] == 1
    assert snapshot["experiment"] == observed["experiment"] == (
        "E1c-SQLServer-Worker-Parity"
    )
    assert snapshot["runId"] == run_id and snapshot["jobId"] == job_id
    assert snapshot["artifactId"] == artifact_id
    assert snapshot["sourceCommit"] == source_sha
    assert re.fullmatch(r"[0-9a-f]{40}", snapshot["checkoutCommit"])
    assert snapshot["url"].endswith("/" + str(run_id))
    assert snapshot["classification"] == kind
    assert observed["classification"] == "SYNTHETIC_ACCOUNTING_WORKLOAD_NOT_CAPACITY"
    assert observed["status"] == "PASS"
    assert observed["controls"] == {
        "eightUniformHotWorkerCases": "PASS",
        "bothCandidatesCommitAll960": "PASS",
        "completeFourTableParity": "PASS",
        "sevenIndependentOracleInvariants": "PASS",
    }
    assert observed["workerCounts"] == [1,2,4,8]
    assert observed["patterns"] == ["uniform", "hot"]
    assert observed["totalLogicalOperations"] == 960
    assert observed["operationsPerWorker"] == 32
    assert len(observed["cases"]) == 8
    for idx, case in enumerate(observed["cases"]):
        workers = (1,2,4,8)[idx % 4]
        pattern = ("uniform","hot")[idx // 4]
        count = 32 * workers
        assert (case["pattern"], case["workers"]) == (pattern,workers)
        assert case["operations"] == count
        assert case["referenceCommitted"] == case["sqlServerCommitted"] == count
        assert case["persistedParity"] is True
        assert case["accounts"] == 16
        assert case["operationsPersisted"] == case["outbox"] == count
        assert case["postings"] == 2 * count
        assert len(case["oracle"]) == 7 and all(case["oracle"].values())
    assert observed["sourceSha256"] == hashes, filename
    if filename.endswith("persistent.json"):
        # This is the current worker-mode source for the ongoing draft PR.
        for relative, digest in hashes.items():
            source = ROOT/"lab"/relative
            assert source.is_file(), relative
            assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, relative
    print(filename, ": PASS; source run", run_id, "; 960 committed transfers")

print("E1C OBSERVATION: PASS (16 parity cases, 8 controls, "
      "1205 deadlock, 1222 bounded retries, SNAPSHOT negative, "
      "SERIALIZABLE defense, independent seven-invariant oracle)")
