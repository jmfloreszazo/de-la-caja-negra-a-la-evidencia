"""Adversarial source-neutral channel-hop traces. No real TCP/ATM/issuer evidence."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from network_fault_gate import assess

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "network_fault_fixture.json"


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class SyntheticHopFaults(unittest.TestCase):
    def check(self, edit, expected="REJECT"):
        data = load()
        edit(data)
        result = assess(data)
        self.assertEqual(result["status"], expected, result)
        for flag in ("physicalLinkCutTested", "nativeIssuerLogAuthenticated",
                     "physicalCashJournalAuthenticated", "delegatedStandInAuthority",
                     "automaticAuthorizationAllowed", "automaticDispenseAllowed",
                     "automaticPostingAllowed", "automaticReversalAllowed",
                     "cohortWriterCutoverAuthorized", "productionApproved"):
            self.assertIs(result[flag], False, result)
        self.assertEqual(result["todmG2"], "INCONCLUSIVE")
        self.assertEqual(result["todmG6"], "BLOCK")
        return result

    def test_01_seven_fixture_scenarios_all_consistent(self):
        r = self.check(lambda data: None, "PASS_SYNTHETIC_HOP_CONSISTENCY")
        self.assertEqual(r["outcomes"], {
            "H01": "NO_CORE_AUTHORIZATION_EVIDENCE",
            "H02": "NO_CORE_AUTHORIZATION_EVIDENCE",
            "H03": "AUTHORIZATION_RECOVERED_BY_STATUS",
            "H04": "CASH_UNKNOWN_NO_REDISPENSE",
            "H05": "QUARANTINED_OLD_OWNER_REPLY",
            "H06": "PARTIAL_CASH_RECONCILED_SYNTHETICALLY",
            "H07": "STAND_IN_DENIED",
        })

    def test_02_dropped_atm_request_cannot_be_marked_delivered(self):
        def modify(d):
            d["scenarios"][0]["events"][2]["kind"] = "ATM_SWITCH_DELIVERED"
        self.check(modify)

    def test_03_switch_core_receive_during_partition_refused(self):
        d = lambda x: x["scenarios"][1]["events"][3].update(kind="SWITCH_CORE_DELIVERED")
        self.check(d)

    def test_04_issuer_commit_without_source_request_refused(self):
        def modify(d):
            d["scenarios"][0]["events"][2].update(kind="ISSUER_COMMITTED", link="ISSUER")
            d["scenarios"][0]["issuerDecision"] = "APPROVED"
        self.check(modify)

    def test_05_lost_reply_without_issuer_commit_refused(self):
        def modify(d):
            d["scenarios"][2]["events"][3].update(
                kind="SWITCH_CORE_DROPPED", link="SWITCH_CORE")
            d["scenarios"][2]["issuerDecision"] = "NOT_OBSERVED"
        self.check(modify)

    def test_06_status_query_before_restored_core_path_refused(self):
        def modify(d):
            d["scenarios"][2]["events"][6]["kind"] = "LINK_DOWN"
        self.check(modify)

    def test_07_status_query_with_missing_original_commit_refused(self):
        def modify(d):
            d["scenarios"][2]["events"][3].update(
                kind="ATM_REQUEST_DROPPED", link="ATM_SWITCH")
            d["scenarios"][2]["issuerDecision"] = "NOT_OBSERVED"
        self.check(modify)

    def test_08_original_core_commit_is_not_cash_dispense(self):
        r = self.check(lambda data: None, "PASS_SYNTHETIC_HOP_CONSISTENCY")
        self.assertEqual(r["outcomes"]["H03"], "AUTHORIZATION_RECOVERED_BY_STATUS")
        self.assertFalse(r["automaticDispenseAllowed"])

    def test_09_device_dispatch_before_atm_approval_refused(self):
        def modify(d):
            d["scenarios"][3]["events"][4].update(
                kind="ISSUER_STATUS_CONFIRMED", link="ISSUER")
        self.check(modify)

    def test_10_duplicate_device_dispatch_refused(self):
        def modify(d):
            item = d["scenarios"][3]["events"][5].copy()
            d["scenarios"][3]["events"].insert(6, item)
            for idx, ev in enumerate(d["scenarios"][3]["events"]):
                ev["step"] = idx + 1
        self.check(modify)

    def test_11_unknown_device_without_dispatch_refused(self):
        def modify(d):
            d["scenarios"][3]["events"][5].update(
                kind="LATE_ADVICE", link="SWITCH_CORE")
        self.check(modify)

    def test_12_unknown_cash_cannot_have_fake_zero_journal(self):
        self.check(lambda d: d["scenarios"][3].update(
            deviceJournalId="J-FAKE", deviceDispensedMinor=0), "INVALID")

    def test_13_unknown_cash_cannot_be_booked_to_ledger(self):
        self.check(lambda d: d["scenarios"][3].update(ledgerPostedMinor=6000))

    def test_14_partial_dispense_ledger_mismatch_refused(self):
        self.check(lambda d: d["scenarios"][5].update(ledgerPostedMinor=10000))

    def test_15_device_delivers_more_than_issuer_approved(self):
        self.check(lambda d: d["scenarios"][5].update(deviceDispensedMinor=11000))

    def test_16_final_device_without_journal_id_invalid(self):
        self.check(lambda d: d["scenarios"][5].update(deviceJournalId=None), "INVALID")

    def test_17_duplicate_ledger_post_event_refused(self):
        def modify(d):
            ev = d["scenarios"][5]["events"][-1].copy()
            d["scenarios"][5]["events"].append(ev)
            d["scenarios"][5]["events"][-1]["step"] += 1
        self.check(modify)

    def test_18_late_old_reply_without_cutover_refused(self):
        def modify(d):
            d["scenarios"][4]["activeEpoch"] = "epoch-a"
        self.check(modify)

    def test_19_wrong_cutover_writer_epoch_refused(self):
        self.check(lambda d: d["scenarios"][4]["events"][4].update(
            sourceEpoch="epoch-c"))

    def test_20_old_reply_replays_wrong_new_epoch_refused(self):
        self.check(lambda d: d["scenarios"][4]["events"][5].update(
            sourceEpoch="epoch-b"))

    def test_21_stale_epoch_in_auth_request_refused(self):
        self.check(lambda d: d["scenarios"][3]["events"][2].update(
            sourceEpoch="epoch-previous"))

    def test_22_writer_epoch_changed_without_cutover_witness(self):
        def modify(d):
            d["scenarios"][4]["events"][4].update(
                kind="LINK_DOWN", link="SWITCH_CORE", sourceEpoch="epoch-a")
        self.check(modify)

    def test_23_duplicate_issuer_commit_refused(self):
        def modify(d):
            s = d["scenarios"][5]["events"]
            s.insert(4, dict(s[3]))
            for i, ev in enumerate(s):
                ev["step"] = i + 1
        self.check(modify)

    def test_24_stand_in_attempt_without_core_failure_refused(self):
        self.check(lambda d: d["scenarios"][6]["events"][2].update(
            kind="LINK_UP"))

    def test_25_stand_in_cannot_create_issuer_commit(self):
        def modify(d):
            d["scenarios"][6]["events"][3].update(
                kind="ISSUER_COMMITTED", link="ISSUER")
            d["scenarios"][6]["issuerDecision"] = "APPROVED"
        self.check(modify)

    def test_26_stand_in_cash_effect_refused(self):
        self.check(lambda d: d["scenarios"][6].update(ledgerPostedMinor=3000))

    def test_27_invented_delegation_invalid(self):
        self.check(lambda d: d.update(policy="STANDIN_APPROVED"), "INVALID")

    def test_28_self_asserted_network_execution_invalid(self):
        self.check(lambda d: d.update(nativeNetworkExecution=True), "INVALID")

    def test_29_self_asserted_bank_approval_invalid(self):
        self.check(lambda d: d.update(bankAuthorization=True), "INVALID")

    def test_30_self_asserted_real_device_invalid(self):
        self.check(lambda d: d.update(deviceHardwareObserved=True), "INVALID")

    def test_31_unrecognized_approval_field_invalid(self):
        self.check(lambda d: d.update(cashCutoverApproved=True), "INVALID")

    def test_32_reordered_event_trace_invalid(self):
        self.check(lambda d: d["scenarios"][2]["events"].reverse(), "INVALID")

    def test_33_event_assigned_to_wrong_hop_invalid(self):
        self.check(lambda d: d["scenarios"][2]["events"][3].update(
            link="ATM_SWITCH"), "INVALID")

    def test_34_boolean_amount_is_not_integer_invalid(self):
        self.check(lambda d: d["scenarios"][0].update(amountMinor=True), "INVALID")

    def test_35_duplicate_operations_across_scenarios_refused(self):
        self.check(lambda d: d["scenarios"][1].update(
            operationId=d["scenarios"][0]["operationId"]))

    def test_36_duplicate_device_journal_across_scenarios_refused(self):
        def modify(d):
            d["scenarios"][3]["deviceState"] = "FINAL"
            d["scenarios"][3]["deviceDispensedMinor"] = 6000
            d["scenarios"][3]["deviceJournalId"] = "DEVICE-JOURNAL-006"
        self.check(modify)

    def test_37_no_core_proof_cannot_be_issuer_approved(self):
        self.check(lambda d: d["scenarios"][1].update(issuerDecision="APPROVED"))

    def test_38_cli_positive_exit_zero_and_safe_flags(self):
        run = subprocess.run(
            [sys.executable, str(HERE / "network_fault_gate.py"), str(FIXTURE)],
            capture_output=True, text=True, check=False, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        value = json.loads(run.stdout)
        self.assertEqual(value["status"], "PASS_SYNTHETIC_HOP_CONSISTENCY")
        self.assertFalse(value["automaticAuthorizationAllowed"])

    def test_39_cli_rejected_trace_exit_two(self):
        data = load()
        data["scenarios"][3]["ledgerPostedMinor"] = 6000
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "trace.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(HERE / "network_fault_gate.py"), str(p)],
                capture_output=True, text=True, check=False, timeout=10)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(json.loads(run.stdout)["status"], "REJECT")

    def test_40_cli_invalid_json_exit_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "trace.json"
            p.write_text("{bad", encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(HERE / "network_fault_gate.py"), str(p)],
                capture_output=True, text=True, check=False, timeout=10)
        self.assertEqual(run.returncode, 3, run.stderr)
        self.assertEqual(json.loads(run.stdout)["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
