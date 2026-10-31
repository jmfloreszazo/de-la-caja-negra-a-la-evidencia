"""Negative controls for the brownfield E1/functional capability gap classification."""
import copy
import json
import unittest
from pathlib import Path

from gap_gate import GapError, evaluate

CONTRACT = json.loads(Path(__file__).with_name("capability_gap.json").read_text(encoding="utf-8"))


class BrownfieldGapTests(unittest.TestCase):
    def rejects(self, mutate):
        doc = copy.deepcopy(CONTRACT)
        mutate(doc)
        with self.assertRaises(GapError):
            evaluate(doc)

    def test_baseline_remains_unapproved(self):
        result = evaluate(CONTRACT)
        self.assertEqual(result["requirements"], 12)
        self.assertEqual(result["bankApprovedRequirements"], 0)
        self.assertFalse(result["productionEquivalent"])
        self.assertEqual(result["todmG6"], "BLOCK")

    def test_two_capabilities_covered(self):
        self.assertEqual({row["cap"] for row in CONTRACT["capabilities"]},
                         {"CAP-005", "CAP-007"})

    def test_cannot_claim_g6_pass(self):
        self.rejects(lambda d: d.update(g6Authorization="PASS"))

    def test_cannot_claim_verified_production(self):
        self.rejects(lambda d: d.update(classification="BANK_APPROVED"))

    def test_cannot_reclassify_as_greenfield(self):
        self.rejects(lambda d: d.update(context="GREENFIELD_MIGRATION"))

    def test_duplicate_ids_rejected(self):
        self.rejects(lambda d: d["capabilities"][1].update(id="BF-001"))

    def test_forged_evidence_status_rejected(self):
        self.rejects(lambda d: d["capabilities"][1].update(status="PRODUCTION_VERIFIED"))

    def test_technical_evidence_requires_source(self):
        self.rejects(lambda d: d["capabilities"][0].update(sources=[]))

    def test_unknown_not_presented_as_observed(self):
        self.rejects(lambda d: d["capabilities"][4].update(sources=["lab/e1_pg/schema.sql"]))

    def test_missing_reference_rejected(self):
        self.rejects(lambda d: d["capabilities"][0].update(sources=["missing.py"]))

    def test_unsafe_reference_rejected(self):
        self.rejects(lambda d: d["capabilities"][0].update(sources=["../../etc/passwd"]))

    def test_no_blank_acceptance_question(self):
        self.rejects(lambda d: d["capabilities"][6].update(nextGate="  "))

    def test_out_of_scope_capability_rejected(self):
        self.rejects(lambda d: d["capabilities"][0].update(cap="CAP-999"))

    def test_missing_limitations_rejected(self):
        self.rejects(lambda d: d.update(assumptions=[]))

    def test_unreviewed_claim_does_not_become_approved(self):
        doc = copy.deepcopy(CONTRACT)
        doc["capabilities"][4]["nextGate"] = "Invented business owner approval"
        self.assertEqual(evaluate(doc)["bankApprovedRequirements"], 0)


if __name__ == "__main__":
    unittest.main()
