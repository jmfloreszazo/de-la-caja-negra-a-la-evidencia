#!/usr/bin/env python3
"""Read-only E3 preflight. A contract alone never proves measured capacity."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess

POSITIVE = (
    "offeredRequestsPerSecond", "requiredCommittedTransfersPerSecond",
    "p99EndToEndMilliseconds", "batchDeadlineSeconds", "measurementDurationSeconds",
    "requiredLoadWithOneNodeLost",
)
NONNEGATIVE = ("requiredRpoSeconds", "requiredRtoSeconds")
DESCRIPTIONS = (
    "mainframeBaseline", "targetEnvironment", "allowedBusinessRejectionMix",
    "durabilityAndReplicationPolicy", "requiredDatasetAndHotKeyDistribution",
)
FIELDS = (*POSITIVE, *NONNEGATIVE, "maxInfrastructureErrorRate", *DESCRIPTIONS)


def assess(contract):
    if not isinstance(contract, dict):
        raise ValueError("Capacity contract must be a JSON object")
    findings = []
    for field in FIELDS:
        value = contract.get(field)
        if value is None or value == "" or value == {} or value == []:
            findings.append({"field": field, "reason": "Missing required contract value"})
            continue
        if field in (*POSITIVE, *NONNEGATIVE, "maxInfrastructureErrorRate"):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                findings.append({"field": field, "reason": "Expected a finite number, not a boolean or string"})
            elif ((field in POSITIVE and value <= 0) or (field in NONNEGATIVE and value < 0)
                  or (field == "maxInfrastructureErrorRate" and not 0 <= value <= 1)):
                findings.append({"field": field, "reason": "Value is outside its permitted range"})
        elif not ((isinstance(value, str) and value.strip()) or (isinstance(value, dict) and value)):
            findings.append({"field": field, "reason": "Expected a nonempty description or structured object"})
    if contract.get("status") in (None, "", "UNCONFIGURED"):
        findings.append({"field": "status", "reason": "Contract is not configured"})
    return {
        "schemaVersion": 1, "classification": "E3_READINESS_ONLY_NOT_A_CAPACITY_TRIAL",
        "verdict": "INCONCLUSIVE", "release": "BLOCK",
        "readiness": "INCOMPLETE" if findings else "EXTERNAL_REVIEW_REQUIRED",
        "findings": findings,
        "measuredCapacity": None,
        "requiredExternalEvidence": [
            "Owner-approved workload contract and independent approval provenance",
            "Authorized comparable Azure, on-premises and mainframe measurements",
            "Open-loop offered and durably committed operations, including failures",
            "One-node-loss recovery, durability, independent accounting oracle and full cost scope",
        ],
        "limitations": [
            "This command does not invoke Azure, run load or verify approval authenticity.",
            "Even a populated contract cannot produce PASS without independent execution evidence.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=Path(__file__).resolve().parents[1] / "performance-contract.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.contract.read_bytes()
    report = assess(json.loads(raw))
    report.update(contractSha256=hashlib.sha256(raw).hexdigest(),
                  checkerSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  sourceCommit=subprocess.check_output(
                      ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parent, text=True).strip(),
                  ciRunId=None, githubActions="NOT_EXECUTED",
                  checkedUtc=datetime.now(timezone.utc).isoformat())
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report, indent=2))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
