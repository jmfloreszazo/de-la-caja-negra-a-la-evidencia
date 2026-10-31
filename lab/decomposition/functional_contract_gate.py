"""Fail-closed review of functional contracts for clean-room modernization.

The gate verifies inventory structure and evidence readiness. It never certifies
observed banking behavior, regulatory conformity, or migration approval.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

class ContractError(ValueError):
    pass

REQUIRED = {
    "id", "domain", "name", "objective", "trigger", "outcome",
    "exceptions", "invariant", "consistency", "criticality", "status",
    "sources", "owner", "approval", "acceptanceCriteria", "unknowns",
}
CONSISTENCY = {"strong", "mixed", "eventual"}
CRITICALITY = {"low", "medium", "high", "critical"}
STATES = {"HYPOTHESIS_NOT_OBSERVED", "EVIDENCE_GATHERED", "OWNER_REVIEWED"}
PROVENANCE = {"business-interview", "approved-policy", "sampled-observation",
              "historical-incident", "production-reconciliation"}
SOURCE_KEYS = {"kind", "reference", "observedAt", "sha256", "approvedForUse"}
APPROVAL_KEYS = {"reviewer", "decisionRef", "reviewedAt"}
ALLOWED_TOP = {"schemaVersion", "classification", "purpose", "decisionRule", "capabilities"}

def check_catalog(document: dict) -> dict:
    if not isinstance(document, dict) or set(document) != ALLOWED_TOP:
        raise ContractError("Catalog schema must be explicit and complete")
    if document["schemaVersion"] != "functional-discovery-1" or document["classification"] != "REFERENCE_HYPOTHESES_ONLY":
        raise ContractError("Only the declared unverified reference catalog is supported")
    if not all(isinstance(document[k], str) and document[k].strip() for k in ("purpose", "decisionRule")):
        raise ContractError("Purpose and acceptance rule are required")
    capabilities = document["capabilities"]
    if not isinstance(capabilities, list) or not capabilities:
        raise ContractError("Nonempty capability registry required")
    seen = set()
    results = []
    for capability in capabilities:
        if not isinstance(capability, dict) or set(capability) != REQUIRED:
            raise ContractError("Capability has missing or unknown fields")
        ident = capability["id"]
        if not isinstance(ident, str) or not ident.startswith("CAP-") or ident in seen:
            raise ContractError("Capability IDs must be unique and stable")
        seen.add(ident)
        for k in ("domain", "name", "objective", "trigger", "outcome", "invariant"):
            if not isinstance(capability[k], str) or not capability[k].strip():
                raise ContractError(f"{ident}: missing functional contract field {k}")
        for k in ("exceptions", "acceptanceCriteria"):
            values = capability[k]
            if not isinstance(values, list) or not values or not all(isinstance(s, str) and s.strip() for s in values):
                raise ContractError(f"{ident}: {k} must contain nonempty descriptions")
        unknowns = capability["unknowns"]
        if not isinstance(unknowns, list) or not all(isinstance(s, str) and s.strip() for s in unknowns):
            raise ContractError(f"{ident}: invalid uncertainty list")
        if not all(s.strip().lower().startswith(("given ", "dado ")) for s in capability["acceptanceCriteria"]):
            raise ContractError(f"{ident}: acceptance scenarios must begin with Given")
        if capability["consistency"] not in CONSISTENCY or capability["criticality"] not in CRITICALITY:
            raise ContractError(f"{ident}: unsupported consistency or criticality")
        if capability["status"] not in STATES:
            raise ContractError(f"{ident}: unsupported evidence state")
        if not isinstance(capability["sources"], list):
            raise ContractError(f"{ident}: source references must be a list")
        for evidence in capability["sources"]:
            if not isinstance(evidence, dict) or set(evidence) != SOURCE_KEYS:
                raise ContractError(f"{ident}: malformed provenance")
            if evidence["kind"] not in PROVENANCE or evidence["approvedForUse"] is not True:
                raise ContractError(f"{ident}: source not explicitly authorized")
            for k in ("reference", "observedAt", "sha256"):
                if not isinstance(evidence[k], str) or not evidence[k].strip():
                    raise ContractError(f"{ident}: missing source provenance {k}")
        approval = capability["approval"]
        if approval is not None:
            if not isinstance(approval, dict) or set(approval) != APPROVAL_KEYS or not all(
                isinstance(approval[k], str) and approval[k].strip() for k in APPROVAL_KEYS):
                raise ContractError(f"{ident}: invalid owner review metadata")
        if capability["owner"] is not None and (not isinstance(capability["owner"], str) or not capability["owner"].strip()):
            raise ContractError(f"{ident}: invalid business owner")
        blockers = []
        if not capability["sources"]:
            blockers.append("NO_AUTHORIZED_BUSINESS_EVIDENCE")
        if not capability["owner"]:
            blockers.append("NO_ACCOUNTABLE_BUSINESS_OWNER")
        if approval is None:
            blockers.append("NO_DOCUMENTED_OWNER_REVIEW")
        if capability["unknowns"]:
            blockers.append("OPEN_FUNCTIONAL_UNCERTAINTIES")
        if capability["status"] == "HYPOTHESIS_NOT_OBSERVED":
            blockers.append("HYPOTHESIS_ONLY")
        if capability["status"] == "OWNER_REVIEWED" and blockers:
            raise ContractError(f"{ident}: owner-reviewed claim conflicts with missing evidence: {blockers}")
        if capability["status"] == "EVIDENCE_GATHERED" and not capability["sources"]:
            raise ContractError(f"{ident}: evidence-gathered claim has no authorized source")
        # Never call a contract accepted. A person must evaluate quality and
        # independent runtime oracles; this tool cannot infer that approval.
        results.append({
            "id": ident, "name": capability["name"],
            "classification": "NEEDS_EVIDENCE" if blockers else "READY_FOR_INDEPENDENT_REVIEW",
            "blockers": blockers,
            "automaticBusinessApproval": False,
        })
    return {
        "classification": "INVENTORY_QUALITY_GATE_NOT_BUSINESS_VERIFICATION",
        "totalCapabilities": len(results),
        "needsEvidence": sum(x["classification"] == "NEEDS_EVIDENCE" for x in results),
        "readyForIndependentReview": sum(x["classification"] == "READY_FOR_INDEPENDENT_REVIEW" for x in results),
        "automaticApprovedCapabilities": 0,
        "capabilities": results,
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("catalog", type=Path)
    args = p.parse_args()
    try:
        result = check_catalog(json.loads(args.catalog.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(json.dumps({"classification": "INVALID_CATALOG", "reason": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 1 if result["needsEvidence"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
