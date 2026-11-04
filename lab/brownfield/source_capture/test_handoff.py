"""Adversarial synthetic cut/cursor oracle tests; NOT native vendor execution."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from handoff import assess

HERE = Path(__file__).resolve().parent
EXAMPLE = HERE / "handoff.example.json"


def fixture():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


class SyntheticHandoffTests(unittest.TestCase):
    def status(self, transform, expected):
        value = fixture()
        transform(value)
        report = assess(value)
        self.assertEqual(report["status"], expected, report)
        self.assertEqual(report["todmG2"], "INCONCLUSIVE")
        self.assertEqual(report["todmG6"], "BLOCK")
        self.assertFalse(report["productionApproved"])
        self.assertFalse(report["nativeCaptureTestExecuted"])
        self.assertFalse(report["externalEffectsReconciled"])
        self.assertFalse(report["independentCustomerSourceOracle"])
        return report

    def test_01_consistent_synthetic_handoff_only(self):
        r = self.status(lambda d: None, "PASS_SYNTHETIC_HANDOFF_ORACLE")
        self.assertEqual((r["sourceCommits"], r["capturedEvents"]), (5, 3))

    def test_02_missing_tail_event_rejected(self):
        r = self.status(lambda d: d["capture"]["events"].pop(1), "REJECT")
        self.assertIn("CAPTURED_SEQUENCE_GAP_DUPLICATE_OR_REORDER", r["errors"])

    def test_03_duplicate_event_rejected(self):
        def change(d):
            d["capture"]["events"][1] = copy.deepcopy(d["capture"]["events"][0])
        r = self.status(change, "REJECT")
        self.assertIn("CAPTURED_EVENTS_NOT_IDENTICAL_TO_SOURCE_COMMITS", r["errors"])

    def test_04_out_of_order_delivery_rejected(self):
        r = self.status(lambda d: d["capture"]["events"].reverse(), "REJECT")
        self.assertIn("CAPTURED_SEQUENCE_GAP_DUPLICATE_OR_REORDER", r["errors"])

    def test_05_amount_tampering_rejected(self):
        self.status(lambda d: d["capture"]["events"][0].update(amountMinor=1), "REJECT")

    def test_06_transaction_id_substitution_rejected(self):
        self.status(lambda d: d["capture"]["events"][0].update(operationId="TAMPER"), "REJECT")

    def test_07_resume_from_wrong_snapshot_position_rejected(self):
        r = self.status(lambda d: d["capture"].update(resumeAfterSequence=1), "REJECT")
        self.assertIn("RESUME_CURSOR_NOT_EQUAL_SNAPSHOT_CUT", r["errors"])

    def test_08_retention_expired_before_cut_rejected(self):
        r = self.status(lambda d: d["capture"].update(oldestRetainedSequence=4), "REJECT")
        self.assertIn("REQUIRED_JOURNAL_HISTORY_EXPIRED", r["errors"])

    def test_09_snapshot_balances_tampered_but_conserved_rejected(self):
        def change(d):
            d["snapshot"]["balances"]["A1"] += 10
            d["snapshot"]["balances"]["A2"] -= 10
        r = self.status(change, "REJECT")
        self.assertIn("SNAPSHOT_BALANCES_MISMATCH_SOURCE_CUT", r["errors"])

    def test_10_snapshot_cut_moved_without_reconstruct_rejected(self):
        self.status(lambda d: d["snapshot"].update(cutSequence=3), "REJECT")

    def test_11_target_balances_tampered_but_conserved_rejected(self):
        def change(d):
            d["target"]["balances"]["A3"] += 4
            d["target"]["balances"]["A4"] -= 4
        self.status(change, "REJECT")

    def test_12_target_cursor_does_not_match_head_rejected(self):
        r = self.status(lambda d: d["target"].update(appliedSequence=4), "REJECT")
        self.assertIn("TARGET_CURSOR_MISMATCH", r["errors"])

    def test_13_source_clock_and_capture_head_diverge_rejected(self):
        r = self.status(lambda d: d["capture"].update(observedHeadSequence=4), "REJECT")
        self.assertIn("OBSERVED_HEAD_DOES_NOT_MATCH_SOURCE_FIXTURE", r["errors"])

    def test_14_changed_source_epoch_rejected(self):
        self.status(lambda d: d["capture"].update(sourceEpoch="restarted-epoch"), "REJECT")

    def test_15_source_transaction_commit_sequence_gap_rejected(self):
        self.status(lambda d: d["sourceCommits"][1].update(sequence=42), "REJECT")

    def test_16_duplicate_committed_operation_id_rejected(self):
        self.status(lambda d: d["sourceCommits"][1].update(
            operationId=d["sourceCommits"][0]["operationId"]), "REJECT")

    def test_17_aborted_operation_reappears_in_source_rejected(self):
        self.status(lambda d: d["abortedOperationIds"].append("TX03"), "REJECT")

    def test_18_bank_approval_self_assertion_is_invalid(self):
        self.status(lambda d: d.update(customerApproval=True), "INVALID")

    def test_19_native_product_execution_self_assertion_is_invalid(self):
        self.status(lambda d: d.update(nativeCaptureExecuted=True), "INVALID")

    def test_20_unknown_platform_or_customer_claim_invalid(self):
        self.status(lambda d: d.update(sourceFamily="CERTIFIED_FUJITSU_CDC"), "INVALID")
        self.status(lambda d: d.update(classification="ACTUAL_BANK_APPROVAL"), "INVALID")

    def test_21_extra_pass_property_refused(self):
        self.status(lambda d: d.update(passApproved=True), "INVALID")

    def test_22_invalid_account_amount_and_boolean_sequence_refused(self):
        self.status(lambda d: d["initialBalances"].update(A1=-2), "INVALID")
        self.status(lambda d: d["sourceCommits"][0].update(sequence=True), "INVALID")

    def test_23_bad_schema_and_invalid_aborted_list_refused(self):
        self.status(lambda d: d.update(schemaVersion=2), "INVALID")
        self.status(lambda d: d.update(abortedOperationIds="TX-ABORTED"), "INVALID")

    def test_24_cli_valid_fixture_is_only_synthetic_pass(self):
        completed = subprocess.run(
            [sys.executable, str(HERE / "handoff.py"), str(EXAMPLE)],
            text=True, capture_output=True, timeout=10, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "PASS_SYNTHETIC_HANDOFF_ORACLE")
        self.assertFalse(result["productionApproved"])

    def test_25_cli_bad_snapshot_fails_closed_with_exit_2(self):
        doc = fixture()
        doc["capture"]["events"].pop()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "trace.json"
            p.write_text(json.dumps(doc), encoding="utf-8")
            out = subprocess.run(
                [sys.executable, str(HERE / "handoff.py"), str(p)],
                text=True, capture_output=True, timeout=10, check=False)
        self.assertEqual(out.returncode, 2)
        self.assertEqual(json.loads(out.stdout)["status"], "REJECT")

    def test_26_cli_invalid_json_exits_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "trace.json"
            p.write_text("{invalid-json", encoding="utf-8")
            out = subprocess.run(
                [sys.executable, str(HERE / "handoff.py"), str(p)],
                text=True, capture_output=True, timeout=10, check=False)
        self.assertEqual(out.returncode, 3)
        self.assertEqual(json.loads(out.stdout)["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
