"""Conservative merge of independent synthetic static/runtime dependencies."""
from collections import defaultdict

class EvidenceConflict(ValueError):
    pass

FIELDS = {"source", "target", "relation", "evidence", "observedAt", "confidence", "atomicGroup"}

def merge_observations(nodes, sources):
    """Preserve disagreements and provenance; absence of traces proves nothing."""
    known = {n["id"] for n in nodes}
    if len(known) != len(nodes):
        raise EvidenceConflict("Duplicate nodes")
    observations = defaultdict(list)
    for source_name, edges in sources.items():
        if source_name not in ("static", "runtime", "domain-expert") or not isinstance(edges, list):
            raise EvidenceConflict("Unsupported evidence source")
        for edge in edges:
            if not isinstance(edge, dict) or set(edge) != FIELDS:
                raise EvidenceConflict("Incomplete provenance")
            if edge["evidence"] != source_name or edge["source"] not in known or edge["target"] not in known:
                raise EvidenceConflict("Invalid source or endpoint")
            if edge["confidence"] not in ("confirmed", "inferred", "unknown") or not isinstance(edge["observedAt"], str) or not edge["observedAt"]:
                raise EvidenceConflict("Invalid observation details")
            if edge["atomicGroup"] is not None and (not isinstance(edge["atomicGroup"], str) or not edge["atomicGroup"]):
                raise EvidenceConflict("Invalid atomic group")
            key = (edge["source"], edge["target"], edge["relation"])
            observations[key].append(dict(edge))
    result = []
    for key, edges in sorted(observations.items()):
        groups = {e["atomicGroup"] for e in edges}
        confidence = {e["confidence"] for e in edges}
        conflict = len(groups) > 1
        status = "unknown" if conflict or "unknown" in confidence else ("confirmed" if confidence == {"confirmed"} else "inferred")
        result.append({"source": key[0], "target": key[1], "relation": key[2],
                       "confidence": status, "conflict": conflict,
                       "atomicGroups": sorted(g for g in groups if g is not None),
                       "observations": sorted(edges, key=lambda e: (e["evidence"], e["observedAt"]))})
    return {"status": "SYNTHETIC_OBSERVATIONS_ONLY", "dependencies": result,
            "conflicts": sum(e["conflict"] for e in result)}
