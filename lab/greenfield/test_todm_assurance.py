"""Golden Master characterization must not grant TODM business/release approval."""
import copy
import json
import unittest
from pathlib import Path

from todm_assurance import AssuranceError, characterize, evaluate

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "contracts/cap007_cap005_synthetic.json").read_text())
GOLDEN = json.loads((HERE / "contracts/golden_master_synthetic.json").read_text())

class TodmAndGoldenMasterTests(unittest.TestCase):
    def good(self):
        return evaluate(CONTRACT, copy.deepcopy(CONTRACT["expected"]), GOLDEN)

    def test_oracle_can_pass_while_release_is_blocked(self):
        result = self.good()
        self.assertEqual(result["gates"]["G5"]["verdict"], "PASS")
        self.assertEqual(result["gates"]["G6"]["verdict"], "BLOCK")
        self.assertFalse(result["productionApproved"])

    def test_golden_master_disagrees_with_policy(self):
        discrepancies = self.good()["goldenMaster"]["disagreements"]
        self.assertEqual(len(discrepancies), 1)
        self.assertEqual(discrepancies[0]["stepIndex"], 8)
        self.assertEqual(discrepancies[0]["characterized"]["status"], "BOOKED")
        self.assertEqual(discrepancies[0]["expected"]["status"], "STALE_PROJECTION")

    def test_matching_characterization_stays_separate(self):
        matches = self.good()["goldenMaster"]["matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["stepIndex"], 2)

    def test_missing_provenance_rejected(self):
        invalid = copy.deepcopy(GOLDEN)
        invalid.pop("sourceId")
        with self.assertRaises(AssuranceError):
            characterize(CONTRACT, invalid)

    def test_production_evidence_claim_from_synthetic_rejected(self):
        invalid = copy.deepcopy(GOLDEN)
        invalid["classification"] = "REAL_PRODUCTION_OBSERVATION"
        with self.assertRaises(AssuranceError):
            characterize(CONTRACT, invalid)

    def test_duplicate_golden_observations_rejected(self):
        invalid = copy.deepcopy(GOLDEN)
        invalid["observations"].append(copy.deepcopy(invalid["observations"][0]))
        with self.assertRaises(AssuranceError):
            characterize(CONTRACT, invalid)

    def test_arbitrary_output_fields_rejected(self):
        invalid = copy.deepcopy(GOLDEN)
        invalid["observations"][0]["observed"]["approvedBy"] = "agent"
        with self.assertRaises(AssuranceError):
            characterize(CONTRACT, invalid)

    def test_bad_candidate_fails_independent_oracle_and_release(self):
        candidate = copy.deepcopy(CONTRACT["expected"])
        candidate["balances"]["A"] += 10
        result = evaluate(CONTRACT, candidate, GOLDEN)
        self.assertEqual(result["gates"]["G5"]["verdict"], "FAIL")
        self.assertEqual(result["gates"]["G6"]["verdict"], "BLOCK")

    def test_green_oracle_does_not_approve_g2_or_g3(self):
        result = self.good()
        self.assertEqual(result["gates"]["G2"]["verdict"], "INCONCLUSIVE")
        self.assertEqual(result["gates"]["G3"]["verdict"], "INCONCLUSIVE")

    def test_modifying_golden_does_not_rewrite_business_oracle(self):
        bad_golden = copy.deepcopy(GOLDEN)
        bad_golden["observations"][1]["observed"]["balance"] = 6000
        original = self.good()
        updated = evaluate(CONTRACT, copy.deepcopy(CONTRACT["expected"]), bad_golden)
        self.assertNotEqual(original["goldenMaster"]["captureFingerprintSha256"],
                            updated["goldenMaster"]["captureFingerprintSha256"])
        self.assertEqual(updated["gates"]["G5"]["verdict"], "PASS")
        self.assertEqual(updated["gates"]["G6"]["verdict"], "BLOCK")

    def test_zero_observations_rejected(self):
        bad = copy.deepcopy(GOLDEN)
        bad["observations"] = []
        with self.assertRaises(AssuranceError):
            characterize(CONTRACT, bad)

    def test_all_eight_gates_are_reported(self):
        result = self.good()
        self.assertEqual(set(result["gates"]), {"G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7"})

if __name__ == "__main__":
    unittest.main()
