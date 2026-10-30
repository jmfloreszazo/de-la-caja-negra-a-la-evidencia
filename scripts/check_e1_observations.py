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

print("E1 OBSERVATION SNAPSHOTS: PASS")
