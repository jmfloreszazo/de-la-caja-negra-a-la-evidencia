"""Adversarial graph boundary cases: false positives must fail closed."""
import copy
import json
import unittest
from pathlib import Path
from oracle import analyze, InvalidEvidence
from boundary_pipeline import analyze_observations

BASE = json.loads(Path(__file__).with_name("fixture.json").read_text(encoding="utf-8"))

def grouped(edges):
    result = {"static": [], "runtime": [], "domain-expert": []}
    for edge in edges:
        result[edge["evidence"]].append(copy.deepcopy(edge))
    return result

class AdversarialExtractionTests(unittest.TestCase):
    def test_hyperedge_disconnected_pairs_are_one_authority(self):
        graph = copy.deepcopy(BASE)
        graph["nodes"].append({"id": "EXTRA_ATOMIC_MEMBER", "kind": "table", "owner": "Ledger"})
        graph["edges"].append(dict(graph["edges"][1], source="OUTBOX",
                                   target="EXTRA_ATOMIC_MEMBER",
                                   observedAt="synthetic-hyperedge"))
        graph["proposals"] = [{"id": "extract-outbox-alone", "extracted": ["OUTBOX"],
                               "approvedAtomicGroups": []}]
        result = analyze(graph)["proposals"][0]
        self.assertEqual(result["decision"], "REJECT")
        self.assertIn("transfer-commit", result["atomicGroupsSplit"])

    def test_inferred_crossing_is_not_approved(self):
        graph = copy.deepcopy(BASE)
        graph["edges"][-1]["confidence"] = "inferred"
        result = analyze(graph)["proposals"][0]
        self.assertEqual(result["decision"], "REJECT")
        self.assertEqual(result["inferredCrossingEdges"], 1)

    def test_unrelated_unknown_does_not_invalidate_other_cut(self):
        graph = copy.deepcopy(BASE)
        graph["edges"][0]["confidence"] = "unknown"
        result = analyze(graph)["proposals"][0]
        self.assertEqual(result["decision"], "CANDIDATE_ONLY")

    def test_conflicting_same_side_claim_rejects_candidate(self):
        graph = copy.deepcopy(BASE)
        evidence = grouped(graph["edges"])
        edge = graph["edges"][3]
        evidence["runtime"].append(dict(edge, evidence="runtime",
                                        observedAt="synthetic-contradiction",
                                        atomicGroup="different-claim"))
        result = analyze_observations(graph["nodes"], evidence, graph["proposals"])
        self.assertEqual(result["boundary"]["proposals"][0]["decision"], "REJECT")

    def test_unsupported_explicit_atomic_override_rejected(self):
        graph = copy.deepcopy(BASE)
        graph["proposals"][1]["approvedAtomicGroups"] = ["transfer-commit"]
        with self.assertRaises(InvalidEvidence):
            analyze(graph)

    def test_partial_atomic_member_extraction_rejected(self):
        graph = copy.deepcopy(BASE)
        graph["proposals"] = [{"id": "post-outbox", "extracted": ["COBOL_POST", "OUTBOX"],
                               "approvedAtomicGroups": []}]
        result = analyze(graph)["proposals"][0]
        self.assertEqual(result["decision"], "REJECT")
        self.assertIn("transfer-commit", result["atomicGroupsSplit"])

if __name__ == "__main__":
    unittest.main()
