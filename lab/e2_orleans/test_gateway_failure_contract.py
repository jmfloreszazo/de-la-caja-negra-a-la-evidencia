"""Negative controls: unrelated crashes must not qualify as a gateway result."""
import json
import unittest

from gateway_failure_contract import classify_startup_deadline


class GatewayFailureTests(unittest.TestCase):
    def setUp(self):
        self.diagnostic = {"status": "CLIENT_STARTUP_DEADLINE",
                           "phase": "BEFORE_FINANCIAL_DISPATCH", "deadlineSeconds": 20,
                           "financialCommandsDispatched": 0}

    def test_exact_application_phase_and_exit_are_required(self):
        self.assertFalse(classify_startup_deadline(
            74, json.dumps(self.diagnostic))["acknowledgedCommitted"])
        with self.assertRaises(AssertionError):
            classify_startup_deadline(1, json.dumps(self.diagnostic))

    def test_gateway_word_or_outer_timeout_cannot_pass(self):
        for message in ("OrleansLab.dll gateway failed", "TimeoutExpired(..., 70)", "{}"):
            with self.assertRaises(AssertionError):
                classify_startup_deadline(74, message)

    def test_post_dispatch_wrong_deadline_and_boolean_zero_are_rejected(self):
        for key, value in (("phase", "AFTER_DISPATCH"), ("deadlineSeconds", 70),
                           ("financialCommandsDispatched", 1),
                           ("financialCommandsDispatched", False)):
            mutated = dict(self.diagnostic, **{key: value})
            with self.assertRaises(AssertionError):
                classify_startup_deadline(74, json.dumps(mutated))


if __name__ == "__main__":
    unittest.main()
