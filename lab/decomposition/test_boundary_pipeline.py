"""Controls for multi-source evidence crossing the extraction oracle."""
import copy
import json
import unittest
from pathlib import Path
from boundary_pipeline import analyze_observations
from evidence_merge import EvidenceConflict

FIXTURE = json.loads(Path(__file__).with_name("fixture.json").read_text())

def sources(edges):
    grouped = {"static": [], "runtime": [], "domain-expert": []}
    for edge in edges:
        grouped[edge["evidence"]].append(copy.deepcopy(edge))
    return grouped

class BoundaryPipelineTests(unittest.TestCase):
    def test_candidate_and_atomic_negative(self):
        result = analyze_observations(FIXTURE["nodes"], sources(FIXTURE["edges"]), FIXTURE["proposals"])
        self.assertEqual([p["decision"] for p in result["boundary"]["proposals"]],
                         ["CANDIDATE_ONLY", "REJECT"])

    def test_conflicting_provenance_rejects_projection(self):
        grouped = sources(FIXTURE["edges"])
        original = FIXTURE["edges"][-1]
        grouped["static"].append(dict(original, evidence="static",
                                      observedAt="synthetic-static-conflict",
                                      atomicGroup="statement-atomic"))
        result = analyze_observations(FIXTURE["nodes"], grouped, FIXTURE["proposals"])
        projection = result["boundary"]["proposals"][0]
        self.assertEqual(projection["decision"], "REJECT")
        self.assertEqual(projection["conflictingDependencies"], 1)
        self.assertIn("statement-atomic", projection["atomicGroupsSplit"])

    def test_unknown_trace_rejects_crossing(self):
        grouped = sources(FIXTURE["edges"])
        grouped["runtime"][-1]["confidence"] = "unknown"
        result = analyze_observations(FIXTURE["nodes"], grouped, FIXTURE["proposals"])
        self.assertEqual(result["boundary"]["proposals"][0]["decision"], "REJECT")

    def test_missing_trace_does_not_invent_one(self):
        grouped = sources(FIXTURE["edges"])
        grouped["runtime"].clear()
        result = analyze_observations(FIXTURE["nodes"], grouped, FIXTURE["proposals"])
        self.assertEqual(result["mergedEvidence"]["conflicts"], 0)
        self.assertEqual(result["boundary"]["proposals"][0]["decision"], "CANDIDATE_ONLY")

    def test_unsupported_source_rejected(self):
        with self.assertRaises(EvidenceConflict):
            analyze_observations(FIXTURE["nodes"], {"untrusted": []}, FIXTURE["proposals"])

    def test_conflict_inside_extracted_nodes_rejected(self):
        grouped = sources(FIXTURE["edges"])
        edge = FIXTURE["edges"][3] # statement query -> projection, both extracted
        grouped["runtime"].append(dict(edge, evidence="runtime",
                                      observedAt="synthetic-runtime-conflict",
                                      atomicGroup="hidden-same-side"))
        result = analyze_observations(FIXTURE["nodes"], grouped, FIXTURE["proposals"])
        self.assertEqual(result["boundary"]["proposals"][0]["decision"], "REJECT")
        self.assertEqual(result["boundary"]["proposals"][0]["conflictingDependencies"], 1)

if __name__ == "__main__":
    unittest.main()
