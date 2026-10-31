"""Fail-closed, deterministic boundary oracle for synthetic mainframe estates."""
import json
import sys
from pathlib import Path

class InvalidEvidence(ValueError):
    pass

def analyze(data):
    if not isinstance(data, dict) or set(data) != {"schemaVersion", "nodes", "edges", "proposals"} or data["schemaVersion"] != 1:
        raise InvalidEvidence("Unsupported or incomplete graph schema")
    nodes = data["nodes"]
    if not isinstance(nodes, list) or not nodes:
        raise InvalidEvidence("Node inventory required")
    by_id = {}
    for node in nodes:
        if not isinstance(node, dict) or set(node) != {"id", "kind", "owner"}:
            raise InvalidEvidence("Malformed node")
        ident = node["id"]
        if not isinstance(ident, str) or not ident or ident in by_id or not isinstance(node["owner"], str) or not node["owner"]:
            raise InvalidEvidence("Duplicate or invalid node identity")
        by_id[ident] = node
    edges = data["edges"]
    if not isinstance(edges, list):
        raise InvalidEvidence("Edges must be a list")
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != {"source", "target", "relation", "evidence", "observedAt", "confidence", "atomicGroup"}:
            raise InvalidEvidence("Malformed edge provenance")
        if edge["source"] not in by_id or edge["target"] not in by_id or edge["source"] == edge["target"]:
            raise InvalidEvidence("Dangling or self-referential dependency")
        if edge["evidence"] not in ("static", "runtime", "domain-expert") or edge["confidence"] not in ("confirmed", "inferred", "unknown"):
            raise InvalidEvidence("Invalid evidence classification")
        if not isinstance(edge["observedAt"], str) or not edge["observedAt"]:
            raise InvalidEvidence("Missing observation provenance")
        if edge["atomicGroup"] is not None and (not isinstance(edge["atomicGroup"], str) or not edge["atomicGroup"]):
            raise InvalidEvidence("Invalid atomic group")
    proposals = data["proposals"]
    if not isinstance(proposals, list) or not proposals:
        raise InvalidEvidence("Proposals required")
    results = []
    for proposal in proposals:
        if not isinstance(proposal, dict) or set(proposal) != {"id", "extracted", "approvedAtomicGroups"}:
            raise InvalidEvidence("Malformed proposal")
        selected = proposal["extracted"]
        if not isinstance(selected, list) or not selected or len(set(selected)) != len(selected) or not set(selected) <= by_id.keys():
            raise InvalidEvidence("Invalid extracted node set")
        if proposal["approvedAtomicGroups"] != []:
            raise InvalidEvidence("Exception/override mechanism is not supported")
        cut = [edge for edge in edges if (edge["source"] in selected) != (edge["target"] in selected)]
        violations = sorted({e["atomicGroup"] for e in cut if e["atomicGroup"] is not None})
        unknown = sum(e["confidence"] == "unknown" for e in cut)
        results.append({"id": proposal["id"], "decision": "REJECT" if violations or unknown else "CANDIDATE_ONLY", "crossingEdges": len(cut), "atomicGroupsSplit": violations, "unknownCrossingEdges": unknown})
    if len({r["id"] for r in results}) != len(results):
        raise InvalidEvidence("Duplicate proposal IDs")
    return {"status": "DESIGN_ONLY_NOT_RUNTIME_PROOF", "proposals": results}

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 oracle.py fixture.json")
    try:
        result = analyze(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    except (InvalidEvidence, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "INVALID", "reason": str(exc)}))
        raise SystemExit(2) from exc
    print(json.dumps(result, indent=2))
    return 1 if any(p["decision"] == "REJECT" for p in result["proposals"]) else 0

if __name__ == "__main__":
    raise SystemExit(main())
