"""Nine offline contract controls for synthetic observation merging."""
import unittest
from evidence_merge import EvidenceConflict, merge_observations

NODES = [{"id": "A"}, {"id": "B"}]
EDGE = {"source": "A", "target": "B", "relation": "updates",
        "evidence": "static", "observedAt": "synthetic-static-1",
        "confidence": "confirmed", "atomicGroup": "tx1"}

class EvidenceMergeTests(unittest.TestCase):
    def test_single_static(self):
        self.assertEqual(merge_observations(NODES, {"static": [EDGE]})["dependencies"][0]["confidence"], "confirmed")
    def test_matching_runtime_preserves_both(self):
        run = dict(EDGE, evidence="runtime", observedAt="synthetic-run-1")
        self.assertEqual(len(merge_observations(NODES, {"static": [EDGE], "runtime": [run]})["dependencies"][0]["observations"]), 2)
    def test_conflicting_atomic_boundary(self):
        run = dict(EDGE, evidence="runtime", observedAt="synthetic-run-1", atomicGroup=None)
        dep = merge_observations(NODES, {"static": [EDGE], "runtime": [run]})["dependencies"][0]
        self.assertTrue(dep["conflict"])
        self.assertEqual(dep["confidence"], "unknown")
    def test_missing_runtime_is_not_positive_evidence(self):
        self.assertEqual(len(merge_observations(NODES, {"static": [EDGE], "runtime": []})["dependencies"][0]["observations"]), 1)
    def test_unsupported_source(self):
        with self.assertRaises(EvidenceConflict):
            merge_observations(NODES, {"generated": [EDGE]})
    def test_missing_timestamp(self):
        with self.assertRaises(EvidenceConflict):
            merge_observations(NODES, {"static": [dict(EDGE, observedAt="")]})
    def test_dangling_node(self):
        with self.assertRaises(EvidenceConflict):
            merge_observations(NODES, {"static": [dict(EDGE, target="MISSING")]})
    def test_unknown_remains_unknown(self):
        self.assertEqual(merge_observations(NODES, {"static": [dict(EDGE, confidence="unknown")]})["dependencies"][0]["confidence"], "unknown")
    def test_duplicate_nodes(self):
        with self.assertRaises(EvidenceConflict):
            merge_observations(NODES + [NODES[0]], {"static": []})

if __name__ == "__main__":
    unittest.main()
