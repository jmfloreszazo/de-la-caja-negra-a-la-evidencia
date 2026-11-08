"""Offline, digest-bound evidence replay; never a production authorization service."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PureWindowsPath

try:
    from .governance import PIN, demonstrate
    from .e3 import reconcile as reconcile_e3
except ImportError:
    from governance import PIN, demonstrate
    from e3 import reconcile as reconcile_e3

PASS, FAIL, INCONCLUSIVE = "PASS", "FAIL", "INCONCLUSIVE"
INVARIANTS = {"balancedPostings", "conserved", "noPostingsForRejection", "nonnegative",
              "outboxAtomic", "projectionAgrees", "twoPostingsPerCommit"}
SCOPES = {"E1": "postgres-concurrency-slice", "E2": "single-cohost-process-kill",
          "E3": "single-host-exploratory-recovery", "E4": "frozen-case-builder-pilot"}


def aggregate(values):
    values = list(values)
    return FAIL if FAIL in values else INCONCLUSIVE if not values or any(v != PASS for v in values) else PASS


def boolean(value):
    return PASS if value is True else FAIL if value is False else INCONCLUSIVE


def vector(value):
    if not isinstance(value, dict):
        return INCONCLUSIVE
    return aggregate([boolean(value.get(key)) for key in INVARIANTS])


def qualification(before, bad, restored):
    negative = (PASS if isinstance(bad, dict) and set(bad) == INVARIANTS
                and all(type(v) is bool for v in bad.values()) and any(v is False for v in bad.values())
                else FAIL if isinstance(bad, dict) and set(bad) == INVARIANTS else INCONCLUSIVE)
    return aggregate([vector(before), negative, vector(restored)])


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite JSON value")))


def safe_path(root, value):
    if not isinstance(value, str) or not value or ":" in value:
        raise ValueError("Artifact path must be relative")
    windows = PureWindowsPath(value)
    if windows.is_absolute() or windows.drive or any(part in ("..", ".") for part in re.split(r"[\\/]", value)):
        raise ValueError("Unsafe artifact path")
    parts = re.split(r"[\\/]", value)
    reserved = {"CON", "PRN", "AUX", "NUL", *("COM" + str(i) for i in range(1, 10)), *("LPT" + str(i) for i in range(1, 10))}
    if any(not part or part.rstrip(" .") != part or part.split(".")[0].upper() in reserved for part in parts):
        raise ValueError("Ambiguous artifact path")
    candidate = root.joinpath(*parts)
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Artifact escapes bundle root")
    for parent in [candidate, *candidate.parents]:
        if parent == root:
            break
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ValueError("Artifact links are not allowed")
    return resolved


def adapt(experiment, report, documents):
    if not isinstance(report, dict):
        return INCONCLUSIVE, INCONCLUSIVE, ["Report must be an object"]
    checks, qualified, findings = [], INCONCLUSIVE, []
    if report.get("status") in (FAIL, "EXPLORATORY_CHECK_FAILED", "EXPLORATORY_ERROR"):
        checks.append(FAIL)
    try:
        if experiment == "E1":
            if report.get("experiment") != "E1a synthetic PostgreSQL concurrency and independent-oracle slice":
                raise ValueError("Unsupported E1 report shape")
            checks.append(vector(report["controls"]["independentOracle"]["invariants"]))
            checks.extend(control.get("status") if isinstance(control, dict) else INCONCLUSIVE for control in report["controls"].values())
            q = documents.get("qualification", {})
            if q.get("experiment") == "E1b-independent-oracle-negative-control":
                vectors = q.get("vectors", {})
                qualified = qualification(vectors.get("before"), vectors.get("corrupted"), vectors.get("restored"))
        elif experiment == "E2":
            if report.get("experiment") != "E2-Orleans-Actual-Cohost-Process-Kill":
                raise ValueError("Unsupported E2 report shape")
            runs = report["killedRuns"]
            expected = {(route, fault) for route in ("direct", "orleans") for fault in ("kill-before-commit", "kill-after-commit")}
            if not isinstance(runs, list) or len(runs) != 4 or {(r["route"], r["fault"]) for r in runs} != expected:
                raise ValueError("Incomplete or duplicate E2 fault/route coverage")
            for run in runs:
                checks.extend([vector(run.get("independentOracle")), boolean(run.get("finalExactlyOneDurableEffect")),
                               boolean(run.get("exitCode") == -9)])
                expected_counts = {"operations": 0, "postings": 0, "outbox": 0} if run["fault"] == "kill-before-commit" else {"operations": 1, "postings": 2, "outbox": 1}
                checks.append(boolean(run.get("afterKill") == expected_counts))
            q = report.get("negativeSplit", {})
            qualified = qualification(q.get("before"), q.get("unsafeSplit"), q.get("restored"))
        elif experiment == "E3":
            if report.get("classification") != "EXPLORATORY_SYNTHETIC_NOT_E3_CAPACITY_ACCEPTANCE" or report.get("capacityAcceptance") is not False:
                raise ValueError("Unsupported E3 report scope")
            checks.extend([vector(report.get("oracleBefore")), vector(report.get("oracleAfter")),
                           boolean(report.get("reconciliation", {}).get("consistent")),
                           boolean(report.get("recovery", {}).get("recoveredServiceAcknowledgedCommit")),
                           boolean(report.get("survivingServiceAliveAfterLoad")),
                           boolean(report.get("errors") == [])])
            negative = report.get("negativeControl", {})
            detected = negative.get("detected")
            qualified = aggregate([vector(negative.get("restoredOracle")),
                PASS if isinstance(detected, list) and {"twoPostingsPerCommit", "projectionAgrees"}.issubset(detected) else INCONCLUSIVE])
            recomputed, mutation_rejected = reconcile_e3(report, documents)
            checks.extend(boolean(value) for value in recomputed.values())
            qualified = aggregate([qualified, boolean(mutation_rejected)])
            findings.extend("Raw E3 check " + key + ": " + (PASS if value else FAIL) for key, value in recomputed.items())
            findings.append("Exploratory recovery only; no capacity threshold or physical HA acceptance")
        elif experiment == "E4":
            if report.get("classification") != "LIVE_MODEL_BUILDER_PILOT_NOT_E4_ACCEPTANCE":
                raise ValueError("Unsupported E4 report scope")
            declared = report.get("independentGate", {}).get("verdict")
            checks.append(declared if declared in (PASS, FAIL, INCONCLUSIVE) else INCONCLUSIVE)
            observations, contracts = documents.get("observations"), documents.get("cases")
            if not isinstance(observations, list) or not isinstance(contracts, list) or not contracts:
                raise ValueError("Frozen cases and raw observations are required")
            expected = {row["id"]: row["expected"] for row in contracts}
            observed = {row["id"]: row for row in observations}
            if len(expected) != len(contracts) or len(observed) != len(observations) or set(expected) != set(observed):
                raise ValueError("Missing, duplicate, or unknown E4 case IDs")
            for key, value in expected.items():
                if not isinstance(value, str) or not isinstance(observed[key].get("candidate"), str) or not isinstance(observed[key].get("legacy"), str):
                    raise ValueError("Invalid E4 observation")
                checks.append(boolean(observed[key]["candidate"] == value == observed[key]["legacy"]))
            checks.extend([boolean(report.get("protectedUnchanged")), boolean(report.get("cases") == len(contracts))])
            q = documents.get("qualification", {})
            mutants = q.get("candidateGateReports", {})
            qualification_checks = [boolean(q.get("protectedUnchanged"))]
            for mutation in ("none", "round-even", "wrong-threshold", "approve-inactive"):
                rows = documents.get("qualification." + mutation)
                if not isinstance(rows, list) or len(rows) != len(expected):
                    qualification_checks.append(INCONCLUSIVE)
                    continue
                by_id = {row["id"]: row for row in rows}
                if set(by_id) != set(expected) or len(by_id) != len(rows):
                    qualification_checks.append(INCONCLUSIVE)
                    continue
                if any(not isinstance(row.get("candidate"), str) or not isinstance(row.get("legacy"), str) for row in rows):
                    qualification_checks.append(INCONCLUSIVE)
                    continue
                actual = aggregate(boolean(by_id[key]["candidate"] == value == by_id[key]["legacy"]) for key, value in expected.items())
                expected_verdict = PASS if mutation == "none" else FAIL
                qualification_checks.append(boolean(actual == expected_verdict == mutants.get(mutation, {}).get("verdict")))
            qualified = aggregate(qualification_checks)
            findings.append("Recomputed candidate, legacy, and qualification-mutant agreement against every bound frozen case; DEMO_ONLY is not authority")
        else:
            raise ValueError("Unsupported experiment")
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        checks.append(INCONCLUSIVE)
        findings.append(str(exc))
    return aggregate(checks), qualified, findings


def gate(name, verdict, findings, evidence=()):
    return {"gate": name, "verdict": verdict, "findings": list(findings), "evidenceIds": list(evidence)}


def evaluate_entry(entry, root):
    experiment = entry.get("experiment")
    gates, issues, records, documents, digest_set, paths, ids = [], [], [], {}, set(), set(), set()
    scope_ok = (experiment in SCOPES and entry.get("scope") == SCOPES.get(experiment)
                and isinstance(entry.get("risk"), str) and bool(entry["risk"].strip())
                and isinstance(entry.get("limitations"), list) and bool(entry["limitations"]))
    gates.append(gate("G0", PASS if scope_ok else INCONCLUSIVE, ["Explicit bounded scope and risk" if scope_ok else "Missing/unsupported scope, risk, or limitations"]))
    artifacts = entry.get("artifacts", [])
    if not isinstance(artifacts, list):
        artifacts = []
        issues.append("Artifacts must be a list")
    for item in artifacts:
        try:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
                raise ValueError("Invalid artifact entry")
            path = safe_path(root, item["path"])
            normalized = str(path).casefold()
            if item["id"] in ids or normalized in paths:
                raise ValueError("Duplicate artifact ID or path")
            ids.add(item["id"])
            paths.add(normalized)
            if not re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", "")):
                raise ValueError("Invalid SHA256")
            raw = path.read_bytes()
            actual = hashlib.sha256(raw).hexdigest()
            if actual != item["sha256"]:
                raise ValueError("Changed artifact bytes: " + item["id"])
            if item.get("role") not in {"source", "contract", "raw", "report", "qualification"}:
                raise ValueError("Unknown artifact role")
            records.append(dict(item, verifiedSha256=actual, bytes=len(raw)))
            digest_set.add(actual)
            if item.get("document"):
                if item["document"] in documents:
                    raise ValueError("Duplicate document adapter name")
                documents[item["document"]] = strict_json(raw)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            if isinstance(exc, OSError):
                issues.append("Unreadable or missing artifact: " + str(item.get("path", "unknown")))
            else:
                issues.append(str(exc))
    roles = {item["role"] for item in records}
    missing = sorted({"source", "contract", "raw", "report"} - roles)
    if missing:
        issues.append("Missing artifact roles: " + ", ".join(missing))
    report = documents.get("report")
    source_claims = []
    for doc in documents.values():
        if isinstance(doc, dict):
            for key in ("sourceSha256", "protectedSha256"):
                claims = doc.get(key, {})
                if isinstance(claims, dict):
                    source_claims.extend(claims.values())
                else:
                    issues.append("Malformed source digest claims")
            for key in ("candidateSha256", "qualifierSha256", "hostSha256", "binarySha256", "sourceArchiveSha256"):
                if key in doc:
                    source_claims.append(doc[key])
            for key in ("artifactSha256", "runtimeArtifactSha256", "legacyInputSha256"):
                claims = doc.get(key, {})
                if isinstance(claims, dict):
                    source_claims.extend(claims.values())
                else:
                    issues.append("Malformed artifact digest claims")
            if "source" in doc:
                source = doc["source"]
                claims = source.get("fileSha256", {}) if isinstance(source, dict) else None
                if isinstance(claims, dict):
                    source_claims.extend(claims.values())
                    encoded = json.dumps(claims, sort_keys=True).encode()
                    if source.get("sourceSetSha256") != hashlib.sha256(encoded).hexdigest():
                        issues.append("Source set digest mismatch")
                else:
                    issues.append("Malformed source provenance")
    if any(not isinstance(value, str) or value not in digest_set for value in source_claims):
        issues.append("Reported source/contract/candidate digest is not bound to supplied bytes")
    integrity = FAIL if issues else PASS if records else INCONCLUSIVE
    evidence_ids = [item["id"] for item in records]
    gates.append(gate("G1", integrity, issues or ["Exact supplied artifacts verified; hashes do not authenticate their producer"], evidence_ids))
    gates.append(gate("G2", INCONCLUSIVE, ["No external trusted baseline approval verifier configured; local approval fields are not authority"]))
    oracle, qualified, findings = adapt(experiment, report, documents)
    if integrity != PASS or not scope_ok:
        oracle = aggregate([oracle, integrity if integrity != PASS else INCONCLUSIVE])
    gates.append(gate("G3", aggregate([qualified, integrity]), ["Bound negative-control qualification, not universal oracle completeness"], evidence_ids))
    gates.append(gate("G4", integrity, ["Recorded construction/source bytes bound; no builder rerun or deployment performed"], evidence_ids))
    gates.append(gate("G5", oracle, findings or ["Independent invariant evidence evaluated; report status alone is insufficient"], evidence_ids))
    gates.append(gate("G6", INCONCLUSIVE, ["No externally authenticated identity, mandate, validity time, or release-owner approval; BLOCK"]))
    gates.append(gate("G7", INCONCLUSIVE, ["Snapshot integrity checked at replay; continuous drift monitoring and evolution approval not connected"]))
    return {"experiment": experiment, "scope": entry.get("scope"), "limitations": entry.get("limitations", []),
            "oracleVerdict": oracle, "qualificationVerdict": qualified,
            "evaluationVerdict": aggregate([gates[0]["verdict"], integrity, qualified, oracle]),
            "methodologyVerdict": aggregate(g["verdict"] for g in gates),
            "authorityVerdict": INCONCLUSIVE, "releaseOutcome": "BLOCK", "gates": gates,
            "bindings": records, "provenance": entry.get("provenance", {}),
            "rawReportProvenance": {key: report[key] for key in ("sourceCommit", "environment", "classification", "limitations", "source", "utc") if isinstance(report, dict) and key in report}}


def evaluate(manifest, root):
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1 or manifest.get("kind") != "TODM_EVIDENCE_BUNDLE":
        raise ValueError("Unsupported bundle schema")
    if manifest.get("upstreamCommit") != PIN:
        raise ValueError("Bundle must pin the supported TODM revision")
    entries = manifest.get("experiments")
    if not isinstance(entries, list) or not entries or any(not isinstance(e, dict) for e in entries):
        raise ValueError("Experiments must be a nonempty object list")
    experiments = [e.get("experiment") for e in entries]
    if any(not isinstance(value, str) for value in experiments) or len(set(experiments)) != len(experiments):
        raise ValueError("Invalid or duplicate experiment IDs")
    results = [evaluate_entry(entry, Path(root).resolve()) for entry in entries]
    return {"schemaVersion": 1, "classification": "LOCAL_PINNED_TODM_METHODOLOGY_REPLAY_NOT_CERTIFIED_ENGINE",
            "upstreamCommit": PIN, "evaluationVerdict": aggregate(r["evaluationVerdict"] for r in results),
            "methodologyVerdict": aggregate(r["methodologyVerdict"] for r in results),
            "releaseOutcome": "BLOCK", "experiments": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--synthetic-governance", action="store_true")
    args = parser.parse_args()
    try:
        if args.synthetic_governance:
            result = demonstrate()
            code = 0 if result["passed"] else 1
        else:
            if args.manifest is None:
                parser.error("--manifest is required unless --synthetic-governance is selected")
            raw = args.manifest.read_bytes()
            result = evaluate(strict_json(raw), args.root)
            result["manifestSha256"] = hashlib.sha256(raw).hexdigest()
            code = {PASS: 0, FAIL: 1, INCONCLUSIVE: 2}[result["evaluationVerdict"]]
        text = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
        if args.output:
            # Never overwrite an input artifact or previous evidence report.
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(text)
        else:
            print(text, end="")
        return code
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"evaluationVerdict": INCONCLUSIVE, "releaseOutcome": "BLOCK", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
