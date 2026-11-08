"""Execute negative controls on copies of actual evidence; never mutate bundle inputs."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

try:
    from .validate import evaluate, strict_json, safe_path, adapt
    from .governance import demonstrate
except ImportError:
    from validate import evaluate, strict_json, safe_path, adapt
    from governance import demonstrate


def qualify(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output == root or not output.is_relative_to(root):
        raise ValueError("Qualification output must be a new directory strictly inside --root; external output directories are not supported")
    output.mkdir(parents=True, exist_ok=False)
    original = strict_json((root / "manifest.json").read_bytes())
    baseline = evaluate(original, root)
    cases = []
    def record(name, manifest, expected, target_root=root):
        result = evaluate(manifest, target_root)
        actual = result["evaluationVerdict"]
        row = {"case": name, "expectedEvaluationVerdict": expected, "actualEvaluationVerdict": actual,
               "releaseOutcome": result["releaseOutcome"], "passed": actual == expected and result["releaseOutcome"] == "BLOCK"}
        cases.append(row)
        (output / (name + ".json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    e1 = copy.deepcopy(original)
    e1["experiments"] = [e1["experiments"][0]]
    record("actual-e1-positive", e1, "PASS")
    forged = copy.deepcopy(e1)
    forged["experiments"][0].update({"approved": True, "signature": "local-forged-approval", "authority": "PASS",
        "releaseApproval": {"kind": "DEMO_SIMULATED", "approved": True, "approverRole": "release-owner"}})
    record("forged-local-approval", forged, "PASS")
    omitted = copy.deepcopy(e1)
    omitted["experiments"][0]["artifacts"] = [item for item in omitted["experiments"][0]["artifacts"] if item.get("document") != "qualification"]
    record("missing-qualification", omitted, "INCONCLUSIVE")
    omitted = copy.deepcopy(e1)
    report_item = next(item for item in omitted["experiments"][0]["artifacts"] if item.get("document") == "report")
    report_item["path"] = "missing-oracle-report.json"
    record("missing-oracle-file", omitted, "FAIL")
    scratch = output / "control-inputs"
    scratch.mkdir()
    report_original = next(item for item in e1["experiments"][0]["artifacts"] if item.get("document") == "report")
    raw = safe_path(root, report_original["path"]).read_bytes()
    for name, mutate, reseal in (
        ("actual-byte-tamper", lambda data: data + b"\ncorruption", False),
        ("independent-invariant-false", None, True),
    ):
        changed = copy.deepcopy(e1)
        artifact = next(item for item in changed["experiments"][0]["artifacts"] if item.get("document") == "report")
        if mutate:
            changed_raw = mutate(raw)
        else:
            doc = strict_json(raw)
            doc["controls"]["independentOracle"]["invariants"]["conserved"] = False
            changed_raw = json.dumps(doc).encode()
        target = scratch / (name + ".json")
        target.write_bytes(changed_raw)
        artifact["path"] = str(target.relative_to(root))
        if reseal:
            artifact["sha256"] = hashlib.sha256(changed_raw).hexdigest()
        record(name, changed, "FAIL")
    documents = {}
    e3 = next(item for item in original["experiments"] if item["experiment"] == "E3")
    for artifact in e3["artifacts"]:
        if artifact.get("document"):
            documents[artifact["document"]] = strict_json(safe_path(root, artifact["path"]).read_bytes())
    for name, corrupted in (("actual-e3-raw-replay", False), ("actual-e3-posting-deletion", True)):
        docs = copy.deepcopy(documents)
        if corrupted:
            docs["ledger"]["postings"].pop()
        verdict, qualification, findings = adapt("E3", docs["report"], docs)
        expected = "FAIL" if corrupted else "PASS"
        cases.append({"case": name, "expectedOracleVerdict": expected, "actualOracleVerdict": verdict,
                      "qualificationVerdict": qualification, "passed": verdict == expected,
                      "findings": findings, "scope": "Raw adapter, separate from full source/runtime bundle integrity"})
    synthetic = demonstrate()
    (output / "synthetic-governance.json").write_text(json.dumps(synthetic, indent=2) + "\n", encoding="utf-8")
    summary = {"classification": "ACTUAL_BUNDLE_ADAPTER_QUALIFICATION_NOT_PRODUCTION_AUTHORIZATION",
        "baselineEvaluationVerdict": baseline["evaluationVerdict"], "baselineReleaseOutcome": baseline["releaseOutcome"],
        "caseCount": len(cases), "cases": cases, "syntheticGovernanceCases": len(synthetic["cases"]),
        "passed": all(case["passed"] for case in cases) and synthetic["passed"],
        "limitations": ["Qualification can PASS while the actual bundle fails due to missing original runtime bytes.",
                        "Corruptions affect copies only; no original artifact is changed.",
                        "Local execution does not authenticate Azure identity or authorize release."]}
    (output / "qualification.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = qualify(args.root.resolve(), args.output.resolve())
    except (OSError, ValueError) as exc:
        print(json.dumps({"passed": False, "releaseOutcome": "BLOCK", "error": str(exc)}))
        return 2
    print(json.dumps({"passed": result["passed"], "caseCount": result["caseCount"], "baselineEvaluationVerdict": result["baselineEvaluationVerdict"]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
