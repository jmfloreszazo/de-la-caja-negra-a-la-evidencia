"""Functional-first extraction-wave gate; never authorizes production migration.

This intentionally consumes the existing functional-capability catalog, NOT
COBOL/JCL parsers or inferred source-level service boundaries.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from functional_contract_gate import ContractError, check_catalog


class WaveError(ValueError):
    pass


TOP = {"schemaVersion", "classification", "purpose", "dependencies", "waves"}
RELATIONS = {
    "atomic_write", "authoritative_read", "batch_cutoff",
    "unknown_runtime", "external_effect", "reconciliation", "channel_read"
}
MODES = {"READ_ONLY_PROJECTION", "COMMAND_REPLACEMENT", "RETIRE", "EXPOSE_LEGACY"}
EDGE = {"source", "target", "relation", "evidence", "question"}
WAVE = {"id", "sequence", "name", "capabilities", "mode", "sourceAuthority",
        "writesAllowed", "readContract", "predecessors", "uncertainties"}
READ_CONTRACT = {"watermarkRequired", "sourceFallbackRequired",
                 "nonAuthoritative", "noExternalEffects", "idempotentRebuild"}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def assess(catalog, proposal):
    """Separate structural refutation from independent/business acceptance."""
    try:
        capability_gate = check_catalog(catalog)
    except ContractError as error:
        raise WaveError("Invalid functional catalog: " + str(error)) from error
    if not isinstance(proposal, dict) or set(proposal) != TOP:
        raise WaveError("Wave plan must have exact declared top-level keys")
    if proposal["schemaVersion"] != "functional-waves-1":
        raise WaveError("Unsupported wave schema")
    if proposal["classification"] != "SYNTHETIC_BOUNDARY_HYPOTHESES":
        raise WaveError("Only synthetic, not-owner-approved input supported")
    if not _text(proposal["purpose"]):
        raise WaveError("Missing purpose")
    capabilities = {x["id"]: x for x in catalog["capabilities"]}
    if not isinstance(proposal["dependencies"], list):
        raise WaveError("Dependencies must be a list")
    edges = []
    edge_ids = set()
    for edge in proposal["dependencies"]:
        if not isinstance(edge, dict) or set(edge) != EDGE:
            raise WaveError("Dependency has missing or extra fields")
        source, target = edge["source"], edge["target"]
        if (not isinstance(source, str) or not isinstance(target, str)
                or source not in capabilities or target not in capabilities
                or source == target):
            raise WaveError("Dependency must link two distinct declared capabilities")
        if edge["relation"] not in RELATIONS:
            raise WaveError("Unknown dependency relation")
        if edge["evidence"] not in {"HYPOTHESIS", "UNKNOWN"}:
            raise WaveError("No observed or approved evidence may be invented")
        if not _text(edge["question"]):
            raise WaveError("Dependency must state its falsifiable owner question")
        key = (source, target, edge["relation"])
        if key in edge_ids:
            raise WaveError("Duplicate dependency")
        edge_ids.add(key)
        edges.append(edge)
    waves = proposal["waves"]
    if not isinstance(waves, list) or not waves:
        raise WaveError("At least one wave is required")
    ids, order = set(), {}
    results = []
    for wave in waves:
        if not isinstance(wave, dict) or set(wave) != WAVE:
            raise WaveError("Wave has missing or extra fields")
        ident = wave["id"]
        if not _text(ident) or ident in ids:
            raise WaveError("Duplicate or invalid wave ID")
        ids.add(ident)
        if not isinstance(wave["sequence"], int) or isinstance(wave["sequence"], bool) or wave["sequence"] < 1:
            raise WaveError("Invalid sequence")
        if wave["sequence"] in order:
            raise WaveError("Duplicate wave sequence")
        order[wave["sequence"]] = ident
        if not _text(wave["name"]) or wave["mode"] not in MODES:
            raise WaveError("Invalid wave name or mode")
        selected = wave["capabilities"]
        if (not isinstance(selected, list) or not selected
                or any(not isinstance(s, str) for s in selected)
                or len(set(selected)) != len(selected)
                or not set(selected) <= capabilities.keys()):
            raise WaveError("Invalid selected capability set")
        if not isinstance(wave["writesAllowed"], bool):
            raise WaveError("writesAllowed must be boolean")
        if wave["sourceAuthority"] not in {"LEGACY", "CANDIDATE"}:
            raise WaveError("Unknown source authority")
        if (not isinstance(wave["uncertainties"], list)
                or not all(_text(t) for t in wave["uncertainties"])):
            raise WaveError("Invalid uncertainty list")
        if (not isinstance(wave["predecessors"], list)
                or any(not _text(x) for x in wave["predecessors"])
                or len(set(wave["predecessors"])) != len(wave["predecessors"])):
            raise WaveError("Invalid predecessor IDs")
        read = wave["readContract"]
        if read is not None and (not isinstance(read, dict) or set(read) != READ_CONTRACT
                                 or not all(isinstance(x, bool) for x in read.values())):
            raise WaveError("Malformed read projection contract")
        blockers = []
        mode = wave["mode"]
        if mode == "READ_ONLY_PROJECTION":
            if (wave["sourceAuthority"] != "LEGACY" or wave["writesAllowed"]
                    or read is None or not all(read.values())):
                blockers.append("UNSAFE_NONAUTHORITATIVE_READ_CONTRACT")
        elif mode == "EXPOSE_LEGACY":
            if wave["sourceAuthority"] != "LEGACY" or wave["writesAllowed"] or read is not None:
                blockers.append("EXPOSURE_MUST_KEEP_LEGACY_AUTHORITY")
        elif mode == "COMMAND_REPLACEMENT":
            if wave["sourceAuthority"] != "CANDIDATE" or not wave["writesAllowed"] or read is not None:
                blockers.append("INVALID_COMMAND_AUTHORITY")
        else:
            if wave["sourceAuthority"] != "LEGACY" or wave["writesAllowed"] or read is not None:
                blockers.append("INVALID_RETIRE_BOUNDARY")
        crossing = [edge for edge in edges
                    if (edge["source"] in selected) != (edge["target"] in selected)]
        crossing_kinds = sorted(set(x["relation"] for x in crossing))
        unknown = [x for x in crossing if x["relation"] == "unknown_runtime"
                   or x["evidence"] == "UNKNOWN"]
        if unknown:
            blockers.append("UNRESOLVED_RUNTIME_DEPENDENCY")
        if mode in {"COMMAND_REPLACEMENT", "RETIRE"}:
            if any(x["relation"] == "atomic_write" for x in crossing):
                blockers.append("SPLIT_ATOMIC_LEDGER_BOUNDARY")
            if any(x["relation"] == "batch_cutoff" for x in crossing):
                blockers.append("SPLIT_BATCH_CUTOFF_OR_RESTART")
            if any(x["relation"] == "external_effect" for x in crossing):
                blockers.append("UNRECONCILED_EXTERNAL_EFFECT")
            if any(x["relation"] == "reconciliation" for x in crossing):
                blockers.append("UNRECONCILED_FINANCIAL_CONSUMER")
        if mode == "RETIRE" and crossing:
            blockers.append("RETIRE_HAS_DECLARED_CONSUMERS")
        results.append({
            "id": ident, "sequence": wave["sequence"],
            "mode": mode, "capabilities": selected,
            "structuralDecision": "REJECT" if blockers else "CANDIDATE_ONLY",
            "blockers": sorted(set(blockers)),
            "crossingRelations": crossing_kinds,
            "crossingDependencies": len(crossing),
            "catalogClaims": {i: capabilities[i]["status"] for i in selected},
            "missingExternalAcceptance": [
                "OWNER_APPROVED_FUNCTIONAL_POLICY",
                "AUTHORIZED_OBSERVED_RUNTIME_AND_CALENDAR_TRACES",
                "SOURCE_SIDE_WRITER_AND_EXTERNAL_EFFECT_PROOF",
                "INDEPENDENT_ORACLE_AND_NEGATIVE_CONTROLS",
                "CAPACITY_RECOVERY_AND_CUTOVER_ACCEPTANCE"
            ],
            "todmG2": "INCONCLUSIVE",
            "todmG6": "BLOCK",
            "deploymentAuthorized": False,
        })
    for wave in waves:
        ident = wave["id"]
        for prior in wave["predecessors"]:
            if prior not in ids:
                raise WaveError("Unknown predecessor for " + ident)
            source_seq = next(x["sequence"] for x in waves if x["id"] == prior)
            if source_seq >= wave["sequence"]:
                raise WaveError("Predecessor must be an earlier wave for " + ident)
    # No wave may authorize deployment, even if all its graph predicates pass
    # and an edited catalog contains self-asserted owner review fields.
    return {
        "classification": "SYNTHETIC_WAVE_SCREENING_NOT_ACCEPTANCE",
        "catalogTotal": capability_gate["totalCapabilities"],
        "catalogNeedsEvidence": capability_gate["needsEvidence"],
        "proposals": sorted(results, key=lambda p: p["sequence"]),
        "structuralCandidates": sum(r["structuralDecision"] == "CANDIDATE_ONLY" for r in results),
        "rejected": sum(r["structuralDecision"] == "REJECT" for r in results),
        "automaticApprovedWaves": 0,
        "todmG2": "INCONCLUSIVE",
        "todmG6": "BLOCK",
        "deploymentAuthorized": False,
        "evidenceVerification": "NOT_PERFORMED_SYNTHETIC_GRAPH_ONLY",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("plan", type=Path)
    arguments = parser.parse_args()
    try:
        result = assess(
            json.loads(arguments.catalog.read_text(encoding="utf-8")),
            json.loads(arguments.plan.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, WaveError) as error:
        print(json.dumps({"classification": "INVALID", "reason": str(error)}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["rejected"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
