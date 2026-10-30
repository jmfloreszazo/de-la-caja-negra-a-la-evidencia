#!/usr/bin/env python3
"""Fail-closed validation of archived original-run E2-F09 observations.

This checks the transcribed, CI-linked record and the specifically bounded
functional evidence. The immutable original artifact is a separate, linked
GitHub Actions file; the local summary does not replace it.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "evidence/runs/e2-orleans-inflight-sql-commit.json"
record = json.loads(path.read_text(encoding="utf-8"))
expected_oracle = {
    "nonnegative", "conserved", "balancedPostings",
    "twoPostingsPerCommit", "noPostingsForRejection",
    "outboxAtomic", "projectionAgrees",
}

assert record["schemaVersion"] == 1
assert record["status"] == "PASS"
assert record["experiment"] == "E2-F09-SQL-InFlight-Silo-SIGKILL"
assert "SINGLE" in record["classification"] or "ONE_PHYSICAL" in record["classification"]
ref = record["provenance"]
assert ref["sourceRunId"] == 41102529778
assert ref["jobId"] == 124222508322
assert ref["artifactId"] == 12999297273
assert ref["rawFile"] == "e2-inflight-sql-commit.json"
assert re.fullmatch("[a-f0-9]{40}", ref["headSha"])
assert re.fullmatch("[a-f0-9]{64}", ref["artifactZipSha256FromActionsLog"])
assert str(ref["sourceRunId"]) in ref["runUrl"]
assert str(ref["artifactId"]) in ref["originalArtifactUrl"]

cases = record["cases"]
assert {x["case"] for x in cases} == {"pre", "post"}
for observation in cases:
    assert observation["actualSecondaryExitSignal"] == "SIGKILL"
    assert observation["membershipAfterKill"] == {
        "primary": "Active 3", "secondary": "Dead 6"
    }
    assert (observation["committedOperations"],
            observation["postings"], observation["outboxEvents"]) == (2, 4, 2)
    oracle = observation["independentSqlOracle"]
    assert set(oracle) == expected_oracle and all(v is True for v in oracle.values())

pre = next(x for x in cases if x["case"] == "pre")
assert pre["uncommittedPostgreSQLAdvisoryWaitObserved"] is True
assert pre["sqlTransactionRollbackAfterServerDeath"] is True
assert pre["explicitRecoveryStatus"] == "COMMITTED"
assert "pg_stat_activity" in pre["observedBeforeKillVia"]

post = next(x for x in cases if x["case"] == "post")
assert post["sqlCommitCompletedBeforeKill"] is True
assert post["explicitRecoveryStatus"] == "DUPLICATE_COMMITTED"
assert post["uncommittedPostgreSQLAdvisoryWaitObserved"] is False
for limitation in ("single Linux runner", "network partition", "mainframe"):
    assert limitation.casefold() in record["limitations"].casefold(), limitation
print("E2-F09 ARCHIVED OBSERVATION: PASS (2 boundaries, 7x2 oracles, original CI links, single-runner limit)")
