"""Negative controls: network/membership success cannot fake grain placement."""
import unittest
from placement_contract import classify_placement


class PlacementContractTest(unittest.TestCase):
    def membership(self, killed=False):
        return {"rows": [
            ("e2-f10-podman-bridge", "10.78.30.11", 11150, 3, 30050),
            ("e2-f10-podman-bridge", "10.78.30.12", 11151,
             6 if killed else 3, 30051)
        ]}

    def test_true_dual_placement_is_required(self):
        nodes = {i: f"e2f10-{'primary' if i % 2 else 'secondary'}:123"
                 for i in range(1, 17)}
        result = classify_placement(nodes, set(range(1, 17)),
                                    self.membership(), True)
        self.assertTrue(result["placementSatisfiesPrecondition"])
        self.assertFalse(result["bankLedgerEffectClaim"])
        self.assertEqual(result["siloCounts"], {
            "e2f10-primary": 8, "e2f10-secondary": 8
        })

    def test_all_secondary_is_negative_even_when_both_active(self):
        nodes = {i: "e2f10-secondary:8" for i in range(1, 17)}
        result = classify_placement(nodes, set(range(1, 17)),
                                    self.membership(), True)
        self.assertFalse(result["placementSatisfiesPrecondition"])
        self.assertEqual(result["siloCounts"]["e2f10-primary"], 0)
        self.assertEqual(
            result["classification"], "PLACEMENT_PRECONDITION_NOT_SATISFIED"
        )

    def test_all_primary_is_also_negative_before_failure(self):
        nodes = {i: "e2f10-primary:8" for i in range(1, 17)}
        result = classify_placement(nodes, set(range(1, 17)),
                                    self.membership(), True)
        self.assertFalse(result["placementSatisfiesPrecondition"])

    def test_post_kill_single_primary_is_positive(self):
        nodes = {i: "e2f10-primary:8" for i in range(1, 17)}
        result = classify_placement(nodes, set(range(1, 17)),
                                    self.membership(killed=True), False)
        self.assertTrue(result["placementSatisfiesPrecondition"])

    def test_post_kill_secondary_placement_is_negative(self):
        nodes = {i: "e2f10-secondary:8" for i in range(1, 17)}
        result = classify_placement(nodes, set(range(1, 17)),
                                    self.membership(killed=True), False)
        self.assertFalse(result["placementSatisfiesPrecondition"])

    def test_stale_membership_prevents_positive_claim(self):
        nodes = {i: "e2f10-primary:8" for i in range(1, 17)}
        with self.assertRaises(AssertionError):
            classify_placement(nodes, set(range(1, 17)),
                               self.membership(), False)

    def test_unknown_silo_fails(self):
        nodes = {i: "undisclosed-host:8" for i in range(1, 17)}
        with self.assertRaises(AssertionError):
            classify_placement(nodes, set(range(1, 17)),
                               self.membership(), True)

    def test_duplicate_or_missing_accounts_fail(self):
        nodes = {i: "e2f10-primary:8" for i in range(1, 16)}
        with self.assertRaises(AssertionError):
            classify_placement(nodes, set(range(1, 17)),
                               self.membership(), True)

    def test_non_numeric_keys_fail(self):
        nodes = {"oops": "e2f10-primary:8"}
        with self.assertRaises(ValueError):
            classify_placement(nodes, {1}, self.membership(), False)


if __name__ == "__main__":
    unittest.main()
