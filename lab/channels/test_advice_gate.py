"""Adversarial check of fictional ATM network advice versus final cash and postings."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from advice_gate import assess

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "advice_fixture.json"


def sample():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class AdviceGateTests(unittest.TestCase):
    def check(self, change, status):
        data = sample()
        change(data)
        result = assess(data)
        self.assertEqual(result["status"], status, result)
        for key in ("realCardNetworkTested", "physicalDeviceJournalAuthenticated",
                    "originalIssuerDataVerified", "standInDelegationApproved",
                    "safeToAutoDispense", "safeToAutoPost", "safeToAutoReverse",
                    "productionApproved"):
            self.assertIs(result[key], False, result)
        self.assertEqual(result["todmG2"], "INCONCLUSIVE")
        self.assertEqual(result["todmG6"], "BLOCK")
        return result

    def test_01_baseline_partial_unknown_zero_denied_standin(self):
        r = self.check(lambda d: None, "PASS_SYNTHETIC_CORRELATION_ONLY")
        self.assertEqual(r["outcomes"], {
            "CASH-001": "MATCHED_PARTIAL_CASH",
            "CASH-002": "UNKNOWN_REQUIRES_DEVICE_EVIDENCE",
            "CASH-003": "FINAL_ZERO_CASH",
            "CASH-004": "STAND_IN_DENIED",
        })

    def test_02_repeated_identical_network_advice_is_idempotent(self):
        self.check(lambda d: d["networkMessages"].append(
            copy.deepcopy(d["networkMessages"][0])), "PASS_SYNTHETIC_CORRELATION_ONLY")

    def test_03_duplicate_stan_across_terminals_not_financial_identity(self):
        self.check(lambda d: None, "PASS_SYNTHETIC_CORRELATION_ONLY")
        self.assertEqual(sample()["authorizations"][0]["networkTrace"],
                         sample()["authorizations"][1]["networkTrace"])

    def test_04_unknown_journal_not_zero_and_not_posted(self):
        r = self.check(lambda d: None, "PASS_SYNTHETIC_CORRELATION_ONLY")
        self.assertEqual(r["outcomes"]["CASH-002"], "UNKNOWN_REQUIRES_DEVICE_EVIDENCE")

    def test_05_cash_amount_modified_without_ledger_update(self):
        r = self.check(lambda d: d["deviceOutcomes"][0].update(
            dispensedMinor=7000), "REJECT")
        self.assertIn("FINANCIAL_AMOUNT_DIFFERS_FROM_DEVICE_JOURNAL", r["errors"])

    def test_06_posting_without_device_cash_fails(self):
        self.check(lambda d: d["corePostings"].append({
            "operationId": "CASH-002", "postingId": "POST-002",
            "amountMinor": 8000}), "REJECT")

    def test_07_second_posting_for_one_operation_rejected(self):
        self.check(lambda d: d["corePostings"].append({
            "operationId": "CASH-001", "postingId": "POST-DUP",
            "amountMinor": 6000}), "REJECT")

    def test_08_wrong_auth_reference_rejected(self):
        self.check(lambda d: d["networkMessages"][0].update(
            authorizationId="AUTH-999"), "REJECT")

    def test_09_wrong_terminal_reference_rejected(self):
        self.check(lambda d: d["networkMessages"][0].update(
            terminalId="ATM-X"), "REJECT")

    def test_10_wrong_retrieval_reference_rejected(self):
        self.check(lambda d: d["networkMessages"][0].update(
            retrievalReference="RRN-X"), "REJECT")

    def test_11_wrong_stan_context_rejected(self):
        self.check(lambda d: d["networkMessages"][0].update(
            networkTrace="999999"), "REJECT")

    def test_12_same_message_id_new_payload_is_not_idempotent(self):
        self.check(lambda d: d["networkMessages"][1].update(
            amountMinor=5000), "REJECT")

    def test_13_unknown_network_operation_not_allowed_to_post(self):
        self.check(lambda d: d["networkMessages"][0].update(
            operationId="CASH-UNKNOWN"), "REJECT")

    def test_14_late_full_reversal_of_partially_delivered_cash_requires_review(self):
        def change(d):
            r = dict(d["networkMessages"][0])
            r.update(messageId="NET-REV-1", messageType="REVERSAL_REQUEST",
                     amountMinor=10000)
            d["networkMessages"].append(r)
        r = self.check(change, "REJECT")
        self.assertIn("REVERSAL_REQUEST_NEEDS_AUTHORIZED_MANUAL_DECISION", r["errors"])
        self.assertEqual(r["outcomes"]["CASH-001"], "MANUAL_REVIEW_REVERSAL_VS_DEVICE")

    def test_15_advice_conflicting_with_final_zero_cash_rejected(self):
        def change(d):
            d["networkMessages"][3].update(messageType="ADVICE")
        self.check(change, "REJECT")

    def test_16_final_device_requires_journal_id(self):
        self.check(lambda d: d["deviceOutcomes"][0].update(
            deviceJournalId=None), "INVALID")

    def test_17_missing_device_outcome_not_assumed_zero(self):
        self.check(lambda d: d["deviceOutcomes"].pop(0), "REJECT")

    def test_18_command_id_wrong_rejected(self):
        self.check(lambda d: d["deviceOutcomes"][0].update(
            commandId="cash/OTHER"), "REJECT")

    def test_19_unapproved_standin_cannot_authorize(self):
        r = self.check(lambda d: d["authorizations"][3].update(
            decision="APPROVED"), "REJECT")
        self.assertIn("UNAUTHORIZED_STAND_IN_APPROVAL", r["errors"])

    def test_20_self_asserted_approval_cannot_override_gate(self):
        self.check(lambda d: d.update(standInDelegationApproved=True), "INVALID")
        self.check(lambda d: d.update(customerApproval=True), "INVALID")

    def test_21_denied_standin_cannot_have_device_outcome(self):
        def change(d):
            d["deviceOutcomes"].append({
                "operationId":"CASH-004","commandId":"cash/CASH-004",
                "terminalId":"ATM-04","deviceJournalId":"J-004",
                "state":"FINAL","dispensedMinor":3000})
        self.check(change,"REJECT")

    def test_22_journal_reuse_between_devices_rejected(self):
        self.check(lambda d: d["deviceOutcomes"][2].update(
            deviceJournalId="J-001"), "REJECT")

    def test_23_duplicate_posting_id_rejected(self):
        def change(d):
            d["corePostings"].append({
                "operationId":"CASH-003","postingId":"POST-001","amountMinor":5000})
        self.check(change,"REJECT")

    def test_24_network_amount_above_request_rejected(self):
        self.check(lambda d: d["networkMessages"][0].update(
            amountMinor=10001), "REJECT")

    def test_25_unknown_device_cannot_claim_amount(self):
        self.check(lambda d: d["deviceOutcomes"][1].update(
            dispensedMinor=0), "INVALID")

    def test_26_boolean_is_not_valid_amount(self):
        self.check(lambda d: d["authorizations"][0].update(
            requestedMinor=True), "INVALID")

    def test_27_extra_schema_claim_rejected(self):
        self.check(lambda d: d.update(
            bankApproved=True), "INVALID")

    def test_28_invalid_or_cross_epoch_messages_refused(self):
        self.check(lambda d: d.update(sourceEpoch=""), "INVALID")
        self.check(lambda d: d["networkMessages"][0].update(
            sourceEpoch="previous-core-epoch"), "REJECT")
        self.check(lambda d: d["authorizations"][0].update(
            sourceEpoch="previous-core-epoch"), "REJECT")

    def test_29_device_cash_more_than_authorized_rejected(self):
        self.check(lambda d: d["deviceOutcomes"][0].update(
            dispensedMinor=12000), "REJECT")

    def test_30_advice_is_not_automatic_posting(self):
        r = self.check(lambda d: None, "PASS_SYNTHETIC_CORRELATION_ONLY")
        self.assertFalse(r["safeToAutoPost"])
        self.assertFalse(r["safeToAutoReverse"])

    def test_31_cli_valid_baseline_returns_zero(self):
        x = subprocess.run([sys.executable,str(HERE/"advice_gate.py"),str(FIXTURE)],
                           capture_output=True,text=True,check=False,timeout=10)
        self.assertEqual(x.returncode,0,x.stderr)
        self.assertEqual(json.loads(x.stdout)["status"],"PASS_SYNTHETIC_CORRELATION_ONLY")

    def test_32_cli_conflicting_replay_exits_two(self):
        d=sample()
        d["networkMessages"][1]["amountMinor"]=5000
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"fixture.json";p.write_text(json.dumps(d),encoding="utf-8")
            x=subprocess.run([sys.executable,str(HERE/"advice_gate.py"),str(p)],
                             capture_output=True,text=True,timeout=10,check=False)
        self.assertEqual(x.returncode,2,x.stderr)
        self.assertEqual(json.loads(x.stdout)["status"],"REJECT")

    def test_33_cli_bad_json_exits_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"fixture.json";p.write_text("{broken",encoding="utf-8")
            x=subprocess.run([sys.executable,str(HERE/"advice_gate.py"),str(p)],
                             capture_output=True,text=True,timeout=10,check=False)
        self.assertEqual(x.returncode,3,x.stderr)
        self.assertEqual(json.loads(x.stdout)["status"],"INVALID")


if __name__=="__main__":
    unittest.main()
