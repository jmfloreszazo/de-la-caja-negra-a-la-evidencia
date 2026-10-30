#!/usr/bin/env python3
"""Validate E1 CI observations without rewriting historical evidence.

Current-code snapshots are byte-matched to the checked-out lab. Historical
snapshots retain their original run, commit and source hashes even after later
test extensions; they must not be misrepresented as observations of new code.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evidence/runs"

# The first E1b observation is retained verbatim for provenance. Its test
# script predates the separately recorded extended E1b execution.
HISTORICAL_E1B = {
    "sourceCommit": "937f0f87ddbd630def1fd1c3d4e410520b93f9d9",
    "runId": 40919773614,
    "jobId": 123609523741,
    "sourceSha256": {
        "PgBank/Program.cs": "eb61acea9673cf14e999adf2c01a03df418c385dee0e3e1f6d777bbca53f5f32",
        "PgBank/PgBank.csproj": "2ba00aa88740c8903fad8d3cddc3f72f06709b5a7c4ab5abed71b5c40a60f43e",
        "test_dotnet.py": "400b3166e65249d5c8f16b9a4161c18afcd3661a4e48b0d2a99b94ab34dc251e",
    },
}
SNAPSHOTS = [
    ("E1a", "e1a.json", 11, "current"),
    ("E1b", "e1b.json", 7, "historical"),
    ("E1b", "e1b-extended.json", 10, "current"),
]
for name, filename, count, source_mode in SNAPSHOTS:
    record = json.loads((BASE / filename).read_text(encoding="utf-8"))
    data = record["observation"]
    assert record["schemaVersion"] == 1 and record["experiment"] == name
    assert re.fullmatch(r"[0-9a-f]{40}", record["sourceCommit"])
    assert record["runId"] > 0 and record["jobId"] > 0
    assert record["url"].endswith("/" + str(record["runId"]))
    assert record["classification"] == "EXECUTED_SNAPSHOT_NOT_MAINFRAME_BENCHMARK"
    assert data["status"] == "PASS"
    assert len(data["controls"]) == count, (filename, list(data["controls"]))
    assert all(
        (value == "PASS" if isinstance(value, str) else value.get("status") == "PASS")
        for value in data["controls"].values()
    )

    if source_mode == "historical":
        # Preserve the exact old source manifest; do NOT compare it to a newer
        # working tree, overwrite its evidence, or silently promote its tests.
        assert record["sourceCommit"] == HISTORICAL_E1B["sourceCommit"]
        assert record["runId"] == HISTORICAL_E1B["runId"]
        assert record["jobId"] == HISTORICAL_E1B["jobId"]
        assert data["sourceSha256"] == HISTORICAL_E1B["sourceSha256"]
    else:
        for relative, expected in data["sourceSha256"].items():
            original = ROOT / "lab" / "e1_pg" / relative
            assert original.is_file(), original
            actual = hashlib.sha256(original.read_bytes()).hexdigest()
            assert actual == expected, (filename, relative, expected, actual)

    if name == "E1a":
        assert "40P01" in str(data["controls"]["deadlockVictimRetried"])
        assert "40001" in str(data["controls"]["writeSkewPrevented"])
        assert data["controls"]["oracleRejectsCorruptLedger"]["detected"]
    else:
        assert data["parity"]["persistedStateEqual"] is True
        assert data["controls"]["candidateParity"] == "PASS"

    if filename == "e1b-extended.json":
        assert record["runId"] == 41024101879
        assert record["sourceCommit"] == "b84559ce06281eb79909640d69c298ba2f521367"
        assert record["checkoutCommit"] == "aff08cd314f86533bb0976dea5991db613c50130"
        assert record["jobId"] == 123958002435 and record["artifactId"] == 12963205523
        for check in (
            "boundedNpgsqlLockRetry",
            "postTimeoutRecoveryAndIdempotency",
            "dotnetPostingCorruptionRejected",
        ):
            assert data["controls"][check] == "PASS"

    print(
        filename, ": snapshot manifest PASS; run", record["runId"],
        "with", count, "controls;", source_mode, "source policy"
    )

# New standalone reference comparison: unlike the historical E1b record,
# this observed execution directly compares the unchanged SQLite/.NET baseline
# against the PostgreSQL/.NET candidate after every synthetic command.
record = json.loads((BASE / "e1b-reference-parity.json").read_text(encoding="utf-8"))
data = record["observation"]
assert record["schemaVersion"] == 1 and data["schemaVersion"] == 1
assert record["experiment"] == data["experiment"] == "E1b-reference-parity"
assert record["runId"] == 41031578923 and record["jobId"] == 123982315732
assert record["artifactId"] == 12965693127
assert record["sourceCommit"] == "222b10f4ff986c80edc0424e7bf107cd2e4f45b4"
assert re.fullmatch(r"[0-9a-f]{40}", record["checkoutCommit"])
assert record["url"].endswith("/" + str(record["runId"]))
assert record["classification"] == "EXECUTED_SYNTHETIC_FUNCTIONAL_PARITY_NOT_CAPACITY"
assert data["classification"] == "SYNTHETIC_FUNCTIONAL_PARITY_NOT_CAPACITY"
assert data["status"] == "PASS" and len(data["controls"]) == 6
assert all(value == "PASS" for value in data["controls"].values())
expected_cases = (
    "accepted", "duplicate-commit", "id-conflict", "rejected",
    "duplicate-rejection", "rejection-conflict", "invalid-operation-id",
    "invalid-zero", "invalid-self-transfer", "invalid-account",
    "exception-rollback", "process-crash-rollback", "lost-acknowledgment",
    "idempotent-replay", "retry-exception-operation",
    "retry-crashed-operation"
)
assert [case["case"] for case in data["cases"]] == list(expected_cases)
assert all(case["persistedParity"] is True and case["oracle"] == "PASS"
           for case in data["cases"])
assert all(case["accounts"] == 16 for case in data["cases"])
assert data["lockRelease"]["referenceRetriesObserved"] is True
assert data["lockRelease"]["postgresRetrySqlstate"] == "55P03"
assert data["lockRelease"]["candidateRetryCount"] >= 1
assert data["lockRelease"]["persistedParity"] is True
assert data["lockRelease"]["oracle"] == "PASS"
assert len(data["sourceSha256"]) == 5
for relative, expected in data["sourceSha256"].items():
    source = ROOT / "lab" / relative
    assert source.is_file(), source
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected, relative
assert data["environment"]["postgresVersion"].startswith("16.")
assert data["environment"]["dotnetVersion"].startswith("10.")
print("E1b-reference-parity: verified 16 cases + lock-release, original run",
      record["runId"], "and source manifest")

# Full read-only oracle verdict vectors before, during and after an
# independent deliberately corrupted persisted posting.
oracle_record = json.loads((BASE / "e1b-oracle-vectors.json").read_text(encoding="utf-8"))
oracle_data = oracle_record["observation"]
assert oracle_record["schemaVersion"] == oracle_data["schemaVersion"] == 1
assert oracle_record["experiment"] == oracle_data["experiment"] == (
    "E1b-independent-oracle-negative-control"
)
assert oracle_record["runId"] == 41032714628
assert oracle_record["jobId"] == 123986044852
assert oracle_record["artifactId"] == 12967270069
assert oracle_record["sourceCommit"] == "b175041e411db5033aa25596d8c1f99f6f535680"
assert re.fullmatch(r"[0-9a-f]{40}", oracle_record["checkoutCommit"])
assert oracle_record["url"].endswith("/" + str(oracle_record["runId"]))
assert oracle_record["classification"] == "EXECUTED_SYNTHETIC_ACCOUNTING_ORACLE_NOT_CAPACITY"
assert oracle_data["status"] == "PASS" and len(oracle_data["controls"]) == 3
assert all(v == "PASS" for v in oracle_data["controls"].values())
expected_fields = {
    "nonnegative", "conserved", "balancedPostings",
    "twoPostingsPerCommit", "noPostingsForRejection",
    "outboxAtomic", "projectionAgrees"
}
before = oracle_data["vectors"]["before"]
corrupted = oracle_data["vectors"]["corrupted"]
restored = oracle_data["vectors"]["restored"]
assert set(before) == set(corrupted) == set(restored) == expected_fields
assert all(before.values()) and all(restored.values())
assert before == restored
assert {k for k, v in corrupted.items() if v is False} == {
    "balancedPostings", "twoPostingsPerCommit", "projectionAgrees"
}
assert all(isinstance(v, bool) for vector in (before, corrupted, restored)
           for v in vector.values())
assert oracle_data["originalOperationCount"] == 6
assert oracle_data["targetPosting"]["operation"] == "unblocked"
assert len(oracle_data["sourceSha256"]) == 4
for name, expected in oracle_data["sourceSha256"].items():
    source = ROOT / "lab" / "e1_pg" / name
    assert source.is_file(), source
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected, name
print("E1b-oracle-vectors: seven independent invariants, negative "
      "mutation and restoration verified; original run", oracle_record["runId"])

# Preserve the exact observed execution environment, separating the
# temporary pull-request merge checkout from the PR's source HEAD.
runtime_record = json.loads((BASE / "e1b-runtime-manifest.json").read_text(encoding="utf-8"))
runtime = runtime_record["observation"]
assert runtime_record["schemaVersion"] == runtime["schemaVersion"] == 1
assert runtime_record["experiment"] == runtime["experiment"] == "E1b-runtime-provenance"
assert runtime_record["runId"] == 41033595770
assert runtime_record["jobId"] == 123988931673
assert runtime_record["artifactId"] == 12967485208
assert runtime_record["sourceCommit"] == "338ef0292c67812cadfb3e9ab7436dad590dbcf8"
assert runtime_record["url"].endswith("/" + str(runtime_record["runId"]))
assert runtime_record["classification"] == "EXECUTED_RUNTIME_PROVENANCE_NOT_CAPACITY"
assert runtime["status"] == "PASS" and runtime["classification"] == (
    "REPRODUCIBILITY_MANIFEST_NOT_PERFORMANCE_PROOF"
)
assert runtime["github"]["runId"] == runtime_record["runId"]
assert runtime["github"]["sourceHead"] == runtime_record["sourceCommit"]
assert runtime["github"]["checkoutCommit"] == runtime_record["checkoutCommit"]
assert runtime["github"]["event"] == "pull_request"
assert runtime["github"]["checkoutCommit"] != runtime["github"]["sourceHead"]
assert re.fullmatch(r"[0-9a-f]{40}", runtime_record["checkoutCommit"])
assert runtime["host"]["python"].startswith("3.")
assert runtime["host"]["dotnetSdk"].startswith("10.")
assert runtime["host"]["podman"].startswith("podman version ")
assert runtime["database"]["postgres"].startswith("16.")
assert runtime["database"]["sqliteNativeDotnet"]
assert runtime["database"]["sqlitePython"]
assert runtime["database"]["npgsqlPackage"] == "10.0.3"
assert re.fullmatch(r"[0-9a-f]{64}", runtime["container"]["imageId"])
assert runtime["container"]["imageReference"] == "docker.io/library/postgres:16.13"
assert len(runtime["container"]["repoDigests"]) >= 1
assert all(re.fullmatch(r"docker\\.io/library/postgres@sha256:[0-9a-f]{64}", digest)
           for digest in runtime["container"]["repoDigests"])
assert len(runtime["sourceSha256"]) == 6
for name, digest in runtime["sourceSha256"].items():
    source = ROOT / "lab" / name
    assert source.is_file(), source
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, name
print("E1b-runtime-manifest: source HEAD and checkout distinct; "
      "tool versions, image digest, six source hashes checked")

print("E1 OBSERVATION SNAPSHOTS: PASS")
