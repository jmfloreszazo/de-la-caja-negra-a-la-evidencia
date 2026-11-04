"""Negative and structural controls for the source-side authority intake gate."""
import copy
import json
from pathlib import Path
import unittest

from assess import REQUIRED_FAMILIES, REQUIRED_PROOFS, assess

HERE = Path(__file__).resolve().parent
SHA = "a" * 64


def evidence(name):
    return {"uri": "evidence/owner-provided/" + name + ".json", "sha256": SHA}


def complete_declarations():
    """An internally filled form is NEVER a verified bank approval."""
    doc = json.loads((HERE / "intake.example.json").read_text(encoding="utf-8"))
    doc["systemRef"] = "synthetic-hypothetical-source"
    doc["ownerApproval"] = evidence("owner-approval")
    doc["goldenMaster"] = evidence("approved-baseline")
    for family in doc["families"]:
        family["applicability"] = "IN_SCOPE"
        family["evidence"] = evidence(family["id"] + "-inventory")
        family["proofs"] = {p: evidence(family["id"] + "-" + p) for p in REQUIRED_PROOFS}
    return doc


class OwnerReadinessTests(unittest.TestCase):
    def test_actual_sample_fails_closed(self):
        doc = json.loads((HERE / "intake.example.json").read_text(encoding="utf-8"))
        result = assess(doc)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("goldenMaster: owner-supplied independent evidence", result["missing"])
        self.assertEqual(result["coveredFamilies"], sorted(REQUIRED_FAMILIES))
        self.assertFalse(result["productionApproved"])
        self.assertEqual(result["todmG6"], "BLOCK")

    def test_complete_declarations_are_only_ready_for_external_review(self):
        result = assess(complete_declarations())
        self.assertEqual(result["status"], "READY_FOR_INDEPENDENT_REVIEW")
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["evidenceVerification"], "NOT_PERFORMED_DECLARATIONS_ONLY")
        self.assertEqual(result["realIncumbentFence"], "NOT_DEMONSTRATED")
        self.assertEqual(result["todmG2"], "INCONCLUSIVE")
        self.assertEqual(result["todmG6"], "BLOCK")
        self.assertFalse(result["financialEffectsVerified"])

    def test_forged_authority_self_assertion_is_invalid(self):
        doc = complete_declarations()
        doc["todmG6"] = "PASS"
        doc["productionApproved"] = True
        self.assertEqual(assess(doc)["status"], "INVALID")

    def test_missing_one_writer_family_is_not_ready(self):
        doc = complete_declarations()
        doc["families"].pop()
        result = assess(doc)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertTrue(any("family not inventoried" in v for v in result["missing"]))

    def test_duplicate_family_invalid(self):
        doc = complete_declarations()
        doc["families"].append(copy.deepcopy(doc["families"][0]))
        self.assertEqual(assess(doc)["status"], "INVALID")

    def test_out_of_scope_requires_independent_owner_exclusion(self):
        doc = complete_declarations()
        doc["families"][0] = {
            "id": "online_legacy", "applicability": "OUT_OF_SCOPE",
            "evidence": None, "proofs": {}, "notes": "Unverified exclusion",
        }
        self.assertEqual(assess(doc)["status"], "NOT_READY")
        doc["families"][0]["evidence"] = evidence("owner-exclusion")
        self.assertEqual(assess(doc)["status"], "READY_FOR_INDEPENDENT_REVIEW")

    def test_unknown_scope_cannot_smuggle_proof(self):
        doc = complete_declarations()
        doc["families"][1]["applicability"] = "UNKNOWN"
        self.assertEqual(assess(doc)["status"], "INVALID")

    def test_missing_source_fence_proof_blocks_readiness(self):
        doc = complete_declarations()
        del doc["families"][0]["proofs"]["source_enforced_fence"]
        result = assess(doc)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertTrue(any("source_enforced_fence" in x for x in result["missing"]))

    def test_bad_digest_invalid(self):
        doc = complete_declarations()
        doc["goldenMaster"]["sha256"] = "not-a-hash"
        self.assertEqual(assess(doc)["status"], "INVALID")

    def test_unknown_family_invalid(self):
        doc = complete_declarations()
        doc["families"][0]["id"] = "unreviewed-path"
        self.assertEqual(assess(doc)["status"], "INVALID")

    def test_no_file_or_fake_result_yields_authority(self):
        for document in [None, [], {"result": "PASS"}]:
            result = assess(document)
            self.assertEqual(result["status"], "INVALID")
            self.assertEqual(result["todmG6"], "BLOCK")
            self.assertFalse(result["productionApproved"])


if __name__ == "__main__":
    unittest.main()
