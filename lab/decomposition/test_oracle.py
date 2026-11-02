"""Offline independent contract controls; no database or mainframe required."""
import copy
import json
import unittest
from pathlib import Path
from oracle import InvalidEvidence, analyze

FIXTURE = json.loads(Path(__file__).with_name("fixture.json").read_text())

class OracleContractTests(unittest.TestCase):
    def test_positive_projection_candidate_only(self):
        result = analyze(FIXTURE)
        self.assertEqual(result["proposals"][0]["decision"], "CANDIDATE_ONLY")
        self.assertEqual(result["proposals"][0]["atomicGroupsSplit"], [])
    def test_negative_atomic_commit_split(self):
        self.assertEqual(analyze(FIXTURE)["proposals"][1]["decision"], "REJECT")
        self.assertEqual(analyze(FIXTURE)["proposals"][1]["atomicGroupsSplit"], ["transfer-commit"])
    def test_unknown_dependency_fails_closed(self):
        data = copy.deepcopy(FIXTURE)
        data["edges"][-1]["confidence"] = "unknown"
        self.assertEqual(analyze(data)["proposals"][0]["decision"], "REJECT")
    def test_dangling_dependency_rejected(self):
        data = copy.deepcopy(FIXTURE)
        data["edges"][0]["target"] = "MISSING"
        with self.assertRaises(InvalidEvidence):
            analyze(data)
    def test_duplicate_nodes_rejected(self):
        data = copy.deepcopy(FIXTURE)
        data["nodes"].append(copy.deepcopy(data["nodes"][0]))
        with self.assertRaises(InvalidEvidence):
            analyze(data)
    def test_override_is_forbidden(self):
        data = copy.deepcopy(FIXTURE)
        data["proposals"][1]["approvedAtomicGroups"] = ["transfer-commit"]
        with self.assertRaises(InvalidEvidence):
            analyze(data)
    def test_missing_provenance_rejected(self):
        data = copy.deepcopy(FIXTURE)
        data["edges"][0]["observedAt"] = ""
        with self.assertRaises(InvalidEvidence):
            analyze(data)
    def test_duplicate_proposals_rejected(self):
        data = copy.deepcopy(FIXTURE)
        data["proposals"].append(copy.deepcopy(data["proposals"][0]))
        with self.assertRaises(InvalidEvidence):
            analyze(data)

if __name__ == "__main__":
    unittest.main()
