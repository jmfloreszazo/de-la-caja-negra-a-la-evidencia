#!/usr/bin/env python3
"""Strict offline check of E2-F10 Podman namespace original-CI summary.

The complete original JSON with real namespace identities and source hashes
is preserved in GitHub Actions artifact #13010797803, not reconstructed here.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
record = json.loads(
    (ROOT / "evidence/runs/e2-orleans-podman-network.json").read_text(
        encoding="utf-8"
    )
)
assert record["schemaVersion"] == 1
assert record["status"] == "PASS"
assert record["experiment"] == (
    "E2-F10-C01-Podman-Routable-Bridge-Network-Namespaces"
)
assert record["classification"] == (
    "FOUR_INDEPENDENT_NETWORK_NAMESPACES_SINGLE_PHYSICAL_CI_HOST"
)
p = record["provenance"]
assert p["sourceRunId"] == 41126502385
assert p["jobId"] == 124306290392
assert p["artifactId"] == 13010797803
assert p["rawFile"] == "e2-f10-podman-routable-bridge.json"
assert re.fullmatch("[0-9a-f]{40}", p["headSha"])
assert re.fullmatch("[0-9a-f]{64}", p["artifactZipSha256FromActionsLog"])
assert str(p["sourceRunId"]) in p["runUrl"]
assert str(p["artifactId"]) in p["originalArtifactUrl"]

result = record["observations"]
assert result["independentNetworkNamespaceCount"] == 4
assert result["privateContainerAddresses"] == {
    "e2f10-pg": "10.78.30.10",
    "e2f10-primary": "10.78.30.11",
    "e2f10-secondary": "10.78.30.12",
    "e2f10-client": "10.78.30.13",
}
assert result["membershipAfter"] == {
    "primaryPort11150": 3,
    "secondaryPort11151": 6,
    "versionAdvanced": True,
}
assert result["secondaryDeath"] == {"signal": "SIGKILL", "exitCode": 137}
assert result["grainReactivatedOnPrimary"] is True
assert result["stableOperationReplay"] == "DUPLICATE_COMMITTED"
assert result["newTransfer"] == "COMMITTED"
assert result["businessEffects"] == {
    "committedOperations": 3, "postings": 6, "outboxEvents": 3
}
expected = {
    "nonnegative", "conserved", "balancedPostings",
    "twoPostingsPerCommit", "noPostingsForRejection",
    "outboxAtomic", "projectionAgrees",
}
oracle = result["independentSqlOracle"]
assert set(oracle) == expected
assert all(value is True for value in oracle.values())

limitations = record["limitations"].casefold()
for nonclaim in (
    "one physical", "network partition", "database ha", "mainframe"
):
    assert nonclaim in limitations, nonclaim
print("E2-F10 PODMAN ORIGINAL-CI OBSERVATION: PASS (4 netns, 3/6/3, 7/7; no physical HA or partition claim)")
