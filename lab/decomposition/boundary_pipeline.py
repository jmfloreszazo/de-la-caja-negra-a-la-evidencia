"""Fail-closed adapter from multi-source observations to the v1 cut oracle.

This is a synthetic design classifier, not a production transaction oracle.
"""
from evidence_merge import EvidenceConflict, merge_observations
from oracle import InvalidEvidence, analyze

def analyze_observations(nodes, sources, proposals):
    merged = merge_observations(nodes, sources)
    edges = []
    for dep in merged["dependencies"]:
        # Preserve every asserted atomic group in distinct edges. Conflicts are
        # unknown even if any single observation claims the cut is safe.
        groups = dep["atomicGroups"] or [None]
        for group in groups:
            edges.append({
                "source": dep["source"], "target": dep["target"],
                "relation": dep["relation"], "evidence": "domain-expert",
                "observedAt": "merged-synthetic-observations",
                "confidence": "unknown" if dep["conflict"] else dep["confidence"],
                "atomicGroup": group,
            })
    graph = {"schemaVersion": 1, "nodes": nodes, "edges": edges,
             "proposals": proposals}
    decisions = analyze(graph)
    # A conflicting observation is never silently promoted. Reject proposals
    # touching either endpoint even if both endpoints fall on one side.
    for result, proposal in zip(decisions["proposals"], proposals):
        selected = set(proposal["extracted"])
        relevant = [d for d in merged["dependencies"]
                    if d["conflict"] and
                    (d["source"] in selected or d["target"] in selected)]
        result["conflictingDependencies"] = len(relevant)
        if relevant:
            result["decision"] = "REJECT"
    return {"status": "DESIGN_ONLY_NOT_RUNTIME_PROOF",
            "mergedEvidence": merged, "boundary": decisions}
