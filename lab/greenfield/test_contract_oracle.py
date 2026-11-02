"""Deliberately mutated greenfield outputs must be rejected by the separate oracle."""
import copy
import json
import unittest
from pathlib import Path

from contract_oracle import OracleFailure, load_contract, verify

HERE = Path(__file__).resolve().parent
CONTRACT = load_contract(HERE / "contracts" / "cap007_cap005_synthetic.json")

class GreenfieldOracleTests(unittest.TestCase):
    def check_reject(self, mutation):
        data = copy.deepcopy(CONTRACT["expected"])
        mutation(data)
        with self.assertRaises(OracleFailure):
            verify(CONTRACT, data)

    def test_manual_golden_outcomes_are_coherent(self):
        verify(CONTRACT, copy.deepcopy(CONTRACT["expected"]))

    def test_balance_mutation_rejected(self):
        self.check_reject(lambda x: x["balances"].update(A=9999))

    def test_double_posting_rejected(self):
        self.check_reject(lambda x: x["postings"].append(copy.deepcopy(x["postings"][0])))

    def test_unbalanced_posting_rejected(self):
        self.check_reject(lambda x: x["postings"][0].update(delta=-1900))

    def test_forged_commit_after_ambiguous_reply_rejected(self):
        self.check_reject(lambda x: x["results"][6].update(status="APPLIED"))

    def test_stale_projection_masquerading_as_authoritative_rejected(self):
        self.check_reject(lambda x: x["results"][8].update(status="BOOKED", balance=7000))

    def test_unauthorized_transfer_accepted_rejected(self):
        self.check_reject(lambda x: x["results"][5].update(status="APPLIED"))

    def test_duplicate_effect_rejected(self):
        self.check_reject(lambda x: x["outbox"].append("TX-1"))

    def test_missing_outbox_rejected(self):
        self.check_reject(lambda x: x["outbox"].pop())

    def test_wrong_projection_watermark_rejected(self):
        self.check_reject(lambda x: x.update(projectionVersion=3))

    def test_version_forgery_rejected(self):
        self.check_reject(lambda x: x.update(version=3))

    def test_unapproved_fixture_rejected(self):
        bad = copy.deepcopy(CONTRACT)
        bad["classification"] = "PRODUCTION_APPROVED"
        with self.assertRaises(OracleFailure):
            verify(bad, copy.deepcopy(CONTRACT["expected"]))

    def test_unexpected_fields_rejected(self):
        self.check_reject(lambda x: x.update(approvedBy="AI"))

if __name__ == "__main__":
    unittest.main()
