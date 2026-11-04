#!/usr/bin/env python3
"""Fail-closed structural intake for a real source-side brownfield writer fence.

This DOES NOT verify evidence bytes, signatures, financial semantics, incumbent
enforcement or business authority. It never returns TODM G2/G6 PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

REQUIRED_FAMILIES = (
    "online_legacy",
    "batch_scheduler",
    "channels",
    "branches_offline",
    "asynchronous_replay",
    "privileged_operations",
    "external_effects",
)
REQUIRED_PROOFS = (
    "source_enforced_fence",
    "inflight_unknown",
    "idempotent_replay",
    "sql_reconciliation",
    "external_effect_reconciliation",
)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
FORBIDDEN = {"todmG2", "todmG6", "businessAccepted", "productionApproved",
             "pass", "result", "releaseApproved"}


def _declared_evidence(value):
    """Validate declarations only; never treat a URI or hash as verified proof."""
    return (isinstance(value, dict) and set(value) == {"uri", "sha256"}
            and isinstance(value["uri"], str)
            and (value["uri"].startswith("https://")
                 or value["uri"].startswith("evidence/"))
            and len(value["uri"]) > 12
            and isinstance(value["sha256"], str)
            and bool(SHA256.fullmatch(value["sha256"])))


def _validate_declared_evidence(value, label, errors, missing):
    if value is None:
        missing.append(label)
    elif not _declared_evidence(value):
        errors.append(label + ": evidence reference must contain URI and lowercase SHA-256")


def assess(document):
    """Return a deterministic readiness report, never banking authorization."""
    errors, missing = [], []
    if not isinstance(document, dict):
        return {"status": "INVALID", "errors": ["Root must be an object"],
                "missing": [], "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
                "productionApproved": False}
    illegal = sorted(FORBIDDEN.intersection(document))
    if illegal:
        errors.append("Input must not self-assert authority: " + ", ".join(illegal))
    expected = {"schemaVersion", "classification", "capabilities", "systemRef",
                "ownerApproval", "goldenMaster", "families"}
    if set(document) != expected:
        errors.append("Unexpected or missing root keys: " + ", ".join(
            sorted(expected.symmetric_difference(document))))
    if document.get("schemaVersion") != 1:
        errors.append("Unsupported schemaVersion")
    if document.get("classification") != "CUSTOMER_SOURCE_DISCOVERY_NOT_VALIDATED":
        errors.append("Source discovery must remain explicitly unvalidated")
    if document.get("capabilities") != ["CAP-005", "CAP-007"]:
        errors.append("This intake is scoped only to CAP-005 and CAP-007")
    system_ref = document.get("systemRef")
    if not isinstance(system_ref, str) or not system_ref.strip():
        missing.append("systemRef: named incumbent system and authority boundary")
    for name in ("ownerApproval", "goldenMaster"):
        value = document.get(name)
        if value is None:
            missing.append(name + ": owner-supplied independent evidence")
        else:
            _validate_declared_evidence(value, name, errors, missing)
    families = document.get("families")
    if not isinstance(families, list):
        errors.append("families must be a list")
        families = []
    seen = set()
    for index, item in enumerate(families):
        if not isinstance(item, dict):
            errors.append(f"families[{index}] must be an object")
            continue
        if set(item) != {"id", "applicability", "evidence", "proofs", "notes"}:
            errors.append(f"families[{index}] unexpected/missing fields")
            continue
        family = item["id"]
        if not isinstance(family, str) or family not in REQUIRED_FAMILIES:
            errors.append(f"families[{index}] unknown writer family")
            continue
        if family in seen:
            errors.append("Duplicate family: " + family)
            continue
        seen.add(family)
        state = item["applicability"]
        if state not in ("UNKNOWN", "IN_SCOPE", "OUT_OF_SCOPE"):
            errors.append(f"{family}: invalid applicability")
            continue
        if not isinstance(item["notes"], str):
            errors.append(f"{family}: notes must be text")
        if state == "UNKNOWN":
            missing.append(f"{family}: determine applicability with source owner")
            # An unknown family must not smuggle proof or exclusions.
            if item["evidence"] is not None or item["proofs"] != {}:
                errors.append(f"{family}: unknown scope cannot assert evidence")
        elif state == "OUT_OF_SCOPE":
            _validate_declared_evidence(item["evidence"], family + ": source-owner exclusion", errors, missing)
            if item["proofs"] != {}:
                errors.append(f"{family}: excluded path cannot assert write proofs")
        else:
            _validate_declared_evidence(item["evidence"], family + ": entrypoint inventory", errors, missing)
            proofs = item["proofs"]
            if not isinstance(proofs, dict):
                errors.append(f"{family}: proofs must be an object")
                continue
            extras = sorted(set(proofs) - set(REQUIRED_PROOFS))
            if extras:
                errors.append(f"{family}: unknown proof keys {extras}")
            for proof in REQUIRED_PROOFS:
                _validate_declared_evidence(proofs.get(proof), f"{family}: {proof}", errors, missing)
    for family in REQUIRED_FAMILIES:
        if family not in seen:
            missing.append(family + ": family not inventoried")
    result = "INVALID" if errors else ("NOT_READY" if missing else "READY_FOR_INDEPENDENT_REVIEW")
    return {
        "status": result,
        "errors": sorted(set(errors)),
        "missing": sorted(set(missing)),
        "coveredFamilies": sorted(seen),
        "evidenceVerification": "NOT_PERFORMED_DECLARATIONS_ONLY",
        "realIncumbentFence": "NOT_DEMONSTRATED",
        "financialEffectsVerified": False,
        "todmG2": "INCONCLUSIVE",
        "todmG6": "BLOCK",
        "productionApproved": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    data = args.path.read_bytes()
    try:
        document = json.loads(data)
    except json.JSONDecodeError:
        document = None
    report = assess(document)
    report["intakeSha256"] = hashlib.sha256(data).hexdigest()
    print(json.dumps(report, sort_keys=True, indent=2))
    return {"READY_FOR_INDEPENDENT_REVIEW": 0, "NOT_READY": 2, "INVALID": 3}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
