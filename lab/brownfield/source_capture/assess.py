#!/usr/bin/env python3
"""Fail-closed native-source change-capture assessment intake.

This validates declarations and question completeness, NEVER source log bytes,
customer identity, installed product capability, security approvals, signatures,
financial reconciliation or banking TODM PASS. Not a COBOL/DDL/parser.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
CATALOG = json.loads((HERE / "capture_catalog.json").read_text(encoding="utf-8"))
SHA256 = re.compile(r"^[a-f0-9]{64}$")
TOP = {"schemaVersion", "classification", "sourceSystem", "ownerApproval",
       "baselineGoldenMaster", "snapshotCutoverPlan", "externalEffectOracle",
       "reconciliationSignoff", "paths"}
PATH_FIELDS = {"family", "applicability", "captureProduct", "productVersion",
               "controls", "outOfScopeEvidence", "ownerQuestions"}
FORBIDDEN = {"todmG2", "todmG6", "businessAccepted", "productionApproved",
             "pass", "bankPass", "releaseApproved", "nativeCdcVerified"}


def _evidence(value) -> bool:
    """Check evidence POINTER shape only. Do not touch the referenced bytes."""
    return (
        isinstance(value, dict) and set(value) == {"uri", "sha256", "claim"}
        and isinstance(value["uri"], str)
        and (value["uri"].startswith("https://")
             or value["uri"].startswith("evidence/"))
        and len(value["uri"]) > 12
        and isinstance(value["sha256"], str)
        and SHA256.fullmatch(value["sha256"]) is not None
        and isinstance(value["claim"], str)
        and len(value["claim"].strip()) >= 12
    )


def _proof(value, label: str, errors: list, missing: list) -> None:
    if value is None:
        missing.append(f"{label}: approved native evidence reference")
    elif not _evidence(value):
        errors.append(f"{label}: invalid evidence pointer; require uri, sha256, claim")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _keys(value, expected, label, errors):
    if not isinstance(value, dict):
        errors.append(f"{label}: must be a JSON object")
        return False
    if set(value) != expected:
        errors.append(f"{label}: unexpected/missing keys {sorted(set(value) ^ expected)}")
        return False
    return True


def assess(record: object, catalog: dict = CATALOG) -> dict:
    """Return structural readiness only; no system/native execution is performed."""
    errors, missing = [], []
    families = catalog["families"]
    common = catalog["genericChecks"]
    if not _keys(record, TOP, "record", errors):
        return _report(errors, missing, {}, catalog)
    if record["schemaVersion"] != 1:
        errors.append("Unsupported schemaVersion")
    if record["classification"] != "CUSTOMER_SOURCE_CAPTURE_DISCOVERY_NOT_VALIDATED":
        errors.append("The intake must remain explicitly NOT_VALIDATED")
    if not _text(record["sourceSystem"]) or record["sourceSystem"].startswith(
            ("UNSPECIFIED", "UNKNOWN", "DEMO")):
        missing.append("sourceSystem: identify actual source, database and release")
    for key in ("ownerApproval", "baselineGoldenMaster", "snapshotCutoverPlan",
                "externalEffectOracle", "reconciliationSignoff"):
        _proof(record[key], key, errors, missing)
    paths = record["paths"]
    if not isinstance(paths, list):
        errors.append("paths: must be a list")
        paths = []
    states = {}
    for i, item in enumerate(paths):
        label = f"paths[{i}]"
        if not _keys(item, PATH_FIELDS, label, errors):
            continue
        family = item["family"]
        if not isinstance(family, str) or family not in families:
            errors.append(f"{label}: unknown capture path family")
            continue
        if family in states:
            errors.append(f"{label}: duplicate path family {family}")
            continue
        state = item["applicability"]
        states[family] = state
        if state not in ("UNKNOWN", "IN_SCOPE", "OUT_OF_SCOPE"):
            errors.append(f"{family}: invalid applicability")
            continue
        questions = item["ownerQuestions"]
        if (not isinstance(questions, list) or not questions
                or any(not _text(q) or len(q.strip()) < 12 for q in questions)):
            errors.append(f"{family}: at least one falsifiable owner question required")
        controls = item["controls"]
        if not isinstance(controls, dict):
            errors.append(f"{family}: controls must be an object")
            continue
        if state == "UNKNOWN":
            missing.append(f"{family}: applicability, actual technology and bypass inventory")
            if (controls or item["captureProduct"] is not None
                    or item["productVersion"] is not None
                    or item["outOfScopeEvidence"] is not None):
                errors.append(f"{family}: UNKNOWN cannot smuggle product/proof/exclusion")
        elif state == "OUT_OF_SCOPE":
            _proof(item["outOfScopeEvidence"],
                   f"{family}: source-owner signed exclusion", errors, missing)
            if controls or item["captureProduct"] is not None or item["productVersion"] is not None:
                errors.append(f"{family}: OUT_OF_SCOPE cannot assert running capture")
        else:
            if item["outOfScopeEvidence"] is not None:
                errors.append(f"{family}: IN_SCOPE cannot assert exclusion simultaneously")
            if not _text(item["captureProduct"]) or not _text(item["productVersion"]):
                missing.append(f"{family}: actual capture product and installed versions")
            required = set(common + families[family]["checks"])
            excess = sorted(set(controls) - required)
            if excess:
                errors.append(f"{family}: undeclared controls {excess}")
            for key in sorted(required):
                _proof(controls.get(key), f"{family}:{key}", errors, missing)
            if not families[family]["documented"]:
                missing.append(f"{family}: vendor-specific primary documents and supported capture mechanism remain NOT_VERIFIED")
    for family in families:
        if family not in states:
            missing.append(f"{family}: capture path not inventoried")
    return _report(errors, missing, states, catalog)


def _report(errors, missing, states, catalog):
    status = "INVALID" if errors else (
        "NOT_READY" if missing else "READY_FOR_INDEPENDENT_REVIEW")
    return {
        "status": status,
        "classification": "STRUCTURAL_SOURCE_CAPTURE_INTAKE_ONLY",
        "errors": sorted(set(errors)),
        "missing": sorted(set(missing)),
        "pathsDeclared": len(states),
        "pathsUnknown": sum(x == "UNKNOWN" for x in states.values()),
        "pathsInScope": sum(x == "IN_SCOPE" for x in states.values()),
        "pathsOutOfScope": sum(x == "OUT_OF_SCOPE" for x in states.values()),
        "primarySourceFamiliesDocumented": sum(
            bool(x["documented"]) for x in catalog["families"].values()),
        "primarySourceFamiliesNotVerified": sorted(
            k for k, v in catalog["families"].items() if not v["documented"]),
        "evidenceBytesVerified": False,
        "nativeCaptureTestExecuted": False,
        "bankSourceWriterFenceProven": False,
        "sourceExternalEffectReconciliationApproved": False,
        "todmG2": "INCONCLUSIVE",
        "todmG6": "BLOCK",
        "productionApproved": False,
        "evidenceDisposition": "REFERENCES_ONLY_NEVER_NATIVE_OR_BANK_PASS",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intake", type=Path)
    parser.add_argument("--catalog", type=Path, default=HERE / "capture_catalog.json")
    arguments = parser.parse_args()
    try:
        record = json.loads(arguments.intake.read_text(encoding="utf-8"))
        catalog = json.loads(arguments.catalog.read_text(encoding="utf-8"))
        if (catalog["schemaVersion"] != 1
                or catalog["classification"] !=
                "DOCUMENTED_VENDOR_PATTERNS_NOT_INSTALLED_OR_TESTED"):
            raise ValueError("Wrong documented pattern catalog classification")
        output = assess(record, catalog)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        output = _report(["Unable to read declared input: " + str(error)], [], {}, CATALOG)
    print(json.dumps(output, sort_keys=True, indent=2))
    return {"READY_FOR_INDEPENDENT_REVIEW": 0, "NOT_READY": 2, "INVALID": 3}[output["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
