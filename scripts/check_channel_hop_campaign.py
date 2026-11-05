#!/usr/bin/env python3
"""Fail-closed evidence intake for an externally run channel hop campaign.

Structural review only. An internally consistent manifest never proves that
its host, fault, network, independent SQL or owner claims are authentic.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

SHA = re.compile(r"^[a-f0-9]{64}$")
REQUIRED_ROLES = ("client", "gateway", "core", "database", "oracle")
REQUIRED_FILES = ("fault_log", "client_log", "gateway_log", "core_log", "sql_snapshot", "oracle_log")
ALLOWED_CASES = ("H01", "H02")
ALLOWED_OUTCOMES = ("PASS", "FAIL", "INCONCLUSIVE")


def audit(path: pathlib.Path) -> dict:
    errors = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"verdict": "INCONCLUSIVE", "errors": [f"unreadable manifest: {exc}"]}
    if not isinstance(manifest, dict):
        return {"verdict": "INCONCLUSIVE", "errors": ["manifest must be an object"]}
    if manifest.get("schemaVersion") != 1:
        errors.append("unsupported schemaVersion")
    if not SHA.fullmatch(str(manifest.get("sourceSha", ""))):
        errors.append("missing exact sourceSha")
    if manifest.get("syntheticDisposable") is not True:
        errors.append("disposable synthetic fixture not established")
    if manifest.get("productionApproved") is not False:
        errors.append("productionApproved must remain false")
    if manifest.get("todmG2") != "INCONCLUSIVE" or manifest.get("todmG6") != "BLOCK":
        errors.append("TODM safety verdicts cannot be promoted")
    roles = manifest.get("hosts", {})
    if not isinstance(roles, dict):
        roles = {}
    for role in REQUIRED_ROLES:
        value = roles.get(role, {})
        if not isinstance(value, dict) or not value.get("hostId") or not value.get("failureDomain"):
            errors.append(f"host/failure-domain identity missing: {role}")
    # Distinct declarations are necessary but NEVER sufficient for physical independence.
    for left, right in (("client", "gateway"), ("gateway", "core"), ("core", "database"), ("oracle", "core")):
        a, b = roles.get(left, {}), roles.get(right, {})
        if isinstance(a, dict) and isinstance(b, dict) and a.get("hostId") and a.get("hostId") == b.get("hostId"):
            errors.append(f"same declared host: {left}/{right}")
    cases = manifest.get("cases", [])
    if not isinstance(cases, list) or sorted(c.get("id") for c in cases if isinstance(c, dict)) != list(ALLOWED_CASES):
        errors.append("exactly one H01 and H02 case required")
        cases = []
    for case in cases:
        if not isinstance(case, dict):
            errors.append("case must be object")
            continue
        ident = case.get("id", "?")
        if case.get("outcome") not in ALLOWED_OUTCOMES:
            errors.append(f"{ident}: unrecognized outcome")
        if case.get("independentSqlOracle") is not True:
            errors.append(f"{ident}: independent SQL observation absent")
        if case.get("unknownAutoAction") is not False or case.get("duplicateFinancialEffects") is not False:
            errors.append(f"{ident}: unsafe action or duplicates not ruled out")
        if not case.get("operationId") or not case.get("injectionWindow"):
            errors.append(f"{ident}: missing operation identity or injection window")
        records = case.get("artifacts", {})
        if not isinstance(records, dict):
            records = {}
        for kind in REQUIRED_FILES:
            record = records.get(kind, {})
            if not isinstance(record, dict):
                record = {}
            rel, digest = record.get("path"), record.get("sha256")
            if not isinstance(rel, str) or not isinstance(digest, str) or not SHA.fullmatch(digest):
                errors.append(f"{ident}: invalid artifact declaration {kind}")
                continue
            raw_path = path.parent / rel
            try:
                resolved = raw_path.resolve(strict=True)
                resolved.relative_to(path.parent.resolve())
                if not resolved.is_file() or resolved.is_symlink():
                    raise ValueError("not a regular in-bundle file")
                actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
                if actual != digest:
                    errors.append(f"{ident}: sha256 mismatch {kind}")
            except (OSError, ValueError):
                errors.append(f"{ident}: unsafe or missing artifact {kind}")
    # Intake never upgrades observations into independent physical or bank sign-off.
    return {
        "verdict": "INCONCLUSIVE" if errors else "READY_FOR_MANUAL_EVIDENCE_REVIEW",
        "errors": errors,
        "physicalIndependenceVerified": False,
        "bankApproved": False,
        "todmG2": "INCONCLUSIVE",
        "todmG6": "BLOCK",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=pathlib.Path)
    args = parser.parse_args()
    result = audit(args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "READY_FOR_MANUAL_EVIDENCE_REVIEW" else 2


if __name__ == "__main__":
    sys.exit(main())
