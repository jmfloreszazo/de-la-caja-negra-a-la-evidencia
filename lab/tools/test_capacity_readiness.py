"""Synthetic preflight controls, not measured capacity evidence."""
import json
from pathlib import Path
import unittest

from check_capacity_readiness import FIELDS, NONNEGATIVE, POSITIVE, assess


class CapacityReadinessTests(unittest.TestCase):
    def test_repository_contract_is_blocked_with_every_missing_field(self):
        path = Path(__file__).resolve().parents[1] / "performance-contract.json"
        report = assess(json.loads(path.read_text()))
        self.assertEqual(report["readiness"], "INCOMPLETE")
        self.assertEqual({row["field"] for row in report["findings"]}, {*FIELDS, "status"})
        self.assertEqual(report["verdict"], "INCONCLUSIVE")
        self.assertEqual(report["release"], "BLOCK")

    def fixture(self):
        contract = dict.fromkeys(FIELDS, "synthetic fixture only")
        contract.update(dict.fromkeys((*POSITIVE, *NONNEGATIVE), 1))
        contract.update(maxInfrastructureErrorRate=0, status="SYNTHETIC_TEST")
        return contract

    def test_filled_contract_never_produces_capacity_acceptance(self):
        report = assess(self.fixture())
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["readiness"], "EXTERNAL_REVIEW_REQUIRED")
        self.assertEqual(report["release"], "BLOCK")
        self.assertIsNone(report["measuredCapacity"])

    def test_invalid_numbers_are_not_filled_values(self):
        for value in (True, "100", float("nan"), float("inf"), -1, 0):
            with self.subTest(value=value):
                contract = self.fixture()
                contract["offeredRequestsPerSecond"] = value
                self.assertEqual(assess(contract)["readiness"], "INCOMPLETE")

    def test_error_rate_is_bounded_and_zero_recovery_targets_are_valid(self):
        contract = self.fixture()
        contract.update(requiredRpoSeconds=0, requiredRtoSeconds=0)
        self.assertFalse(assess(contract)["findings"])
        contract["maxInfrastructureErrorRate"] = 1.01
        self.assertEqual(assess(contract)["findings"][0]["field"], "maxInfrastructureErrorRate")

    def test_missing_fields_and_wrong_shapes_are_not_accepted(self):
        self.assertEqual(assess({})["readiness"], "INCOMPLETE")
        for value in ([], None, "contract"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                assess(value)


if __name__ == "__main__":
    unittest.main()
