"""Offline negative controls: catalog quality is not business verification."""
import copy
import json
import unittest
from pathlib import Path

from functional_contract_gate import ContractError, check_catalog

CATALOG = json.loads(Path(__file__).with_name("functional_capabilities.json").read_text(encoding="utf-8"))


class FunctionalCapabilityContractTests(unittest.TestCase):
    def test_30_hypotheses_none_approved(self):
        result = check_catalog(CATALOG)
        self.assertEqual(result["totalCapabilities"], 30)
        self.assertEqual(result["needsEvidence"], 30)
        self.assertEqual(result["automaticApprovedCapabilities"], 0)

    def test_catalog_explicitly_hypothetical(self):
        self.assertEqual(CATALOG["classification"], "REFERENCE_HYPOTHESES_ONLY")
        self.assertTrue(all(c["status"] == "HYPOTHESIS_NOT_OBSERVED"
                            for c in CATALOG["capabilities"]))

    def test_duplicate_capability_id_rejected(self):
        doc = copy.deepcopy(CATALOG)
        doc["capabilities"][1]["id"] = doc["capabilities"][0]["id"]
        with self.assertRaises(ContractError):
            check_catalog(doc)

    def test_missing_invariant_rejected(self):
        doc = copy.deepcopy(CATALOG)
        doc["capabilities"][0]["invariant"] = ""
        with self.assertRaises(ContractError):
            check_catalog(doc)

    def test_missing_exception_rejected(self):
        doc = copy.deepcopy(CATALOG)
        doc["capabilities"][0]["exceptions"] = []
        with self.assertRaises(ContractError):
            check_catalog(doc)

    def test_unstructured_acceptance_rejected(self):
        doc = copy.deepcopy(CATALOG)
        doc["capabilities"][0]["acceptanceCriteria"] = ["The system should be fast"]
        with self.assertRaises(ContractError):
            check_catalog(doc)

    def test_fake_evidence_status_rejected(self):
        doc = copy.deepcopy(CATALOG)
        doc["capabilities"][0]["status"] = "EVIDENCE_GATHERED"
        with self.assertRaises(ContractError):
            check_catalog(doc)

    def test_fake_approval_status_rejected(self):
        doc = copy.deepcopy(CATALOG)
        doc["capabilities"][0]["status"] = "OWNER_REVIEWED"
        with self.assertRaises(ContractError):
            check_catalog(doc)

    def test_unapproved_provenance_rejected(self):
        doc = copy.deepcopy(CATALOG)
        doc["capabilities"][0]["sources"] = [{
            "kind": "business-interview", "reference": "synthetic-only",
            "observedAt": "2026-10-31", "sha256": "placeholder",
            "approvedForUse": False,
        }]
        with self.assertRaises(ContractError):
            check_catalog(doc)

    def test_complete_metadata_not_automatic_business_approval(self):
        doc = copy.deepcopy(CATALOG)
        item = doc["capabilities"][0]
        item["sources"] = [{
            "kind": "approved-policy", "reference": "invented-example",
            "observedAt": "2026-10-31", "sha256": "0" * 64,
            "approvedForUse": True,
        }]
        item["owner"] = "Hypothetical owner"
        item["approval"] = {
            "reviewer": "Hypothetical reviewer",
            "decisionRef": "synthetic-review",
            "reviewedAt": "2026-10-31",
        }
        item["unknowns"] = []
        item["status"] = "OWNER_REVIEWED"
        result = check_catalog(doc)
        self.assertEqual(result["capabilities"][0]["classification"], "READY_FOR_INDEPENDENT_REVIEW")
        self.assertEqual(result["automaticApprovedCapabilities"], 0)
        self.assertFalse(result["capabilities"][0]["automaticBusinessApproval"])

    def test_no_unknown_fields_allowed(self):
        doc = copy.deepcopy(CATALOG)
        doc["capabilities"][0]["pretendApproved"] = True
        with self.assertRaises(ContractError):
            check_catalog(doc)

    def test_critical_controls_are_identified(self):
        critical = {c["id"] for c in CATALOG["capabilities"] if c["criticality"] == "critical"}
        self.assertTrue({"CAP-007", "CAP-011", "CAP-019", "CAP-020",
                         "CAP-023", "CAP-026", "CAP-029"}.issubset(critical))


if __name__ == "__main__":
    unittest.main()
