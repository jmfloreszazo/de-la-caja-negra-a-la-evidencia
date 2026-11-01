"""Independent negative controls for the synthetic coexistence admission model."""
from dataclasses import replace
import hashlib
import unittest

from coexistence_gate import CutoverBlocked, CutoverEvidence, RehearsalGate


def sha(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def evidence(gate: RehearsalGate) -> CutoverEvidence:
    return CutoverEvidence(
        source_epoch=gate.epoch,
        source_watermark=gate.ledger_watermark,
        target_watermark=gate.ledger_watermark,
        source_balances_sha256=sha("balance-0"), target_balances_sha256=sha("balance-0"),
        source_operations_sha256=sha("operations-0"), target_operations_sha256=sha("operations-0"),
        source_postings_sha256=sha("postings-0"), target_postings_sha256=sha("postings-0"),
        source_outbox_sha256=sha("outbox-0"), target_outbox_sha256=sha("outbox-0"),
        observed_source_count=gate.ledger_watermark,
        observed_target_count=gate.ledger_watermark,
        source_inflight_count=0,
        target_inflight_count=0,
        provenance="synthetic-fixture:paired-ledger-model-v1",
    )


F1, F2 = sha("transfer A B 100; mandate=synthetic"), sha("transfer A B 101; mandate=synthetic")


class CutoverRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.gate = RehearsalGate()

    def test_initial_authority_is_legacy_and_g6_always_blocks_production(self):
        self.assertEqual((self.gate.writer, self.gate.epoch), ("legacy", 1))
        self.assertEqual(self.gate.todm_g6, "BLOCK")
        self.assertFalse(self.gate.business_owner_approved)
        with self.assertRaises(AttributeError):
            self.gate.todm_g6 = "PASS"
        with self.assertRaises(AttributeError):
            self.gate.business_owner_approved = True

    def test_first_command_routes_only_to_legacy(self):
        self.assertEqual(self.gate.route_transfer("TX-1", F1, 1), "ROUTE_LEGACY")
        self.assertEqual(self.gate.operations["TX-1"].writer, "legacy")

    def test_inflight_replay_cannot_create_second_write(self):
        self.gate.route_transfer("TX-1", F1, 1)
        self.assertEqual(self.gate.route_transfer("TX-1", F1, 1), "IN_FLIGHT_RETRY_BLOCKED")
        self.assertEqual(len(self.gate.operations), 1)

    def test_rejected_replay_is_stable_and_does_not_increment_watermark(self):
        self.gate.route_transfer("TX-1", F1, 1)
        self.gate.record_outcome("TX-1", "REJECTED")
        self.assertEqual(self.gate.route_transfer("TX-1", F1, 1), "DUPLICATE_REJECTED")
        self.assertEqual(self.gate.ledger_watermark, 0)

    def test_committed_replay_has_no_second_effect(self):
        self.gate.route_transfer("TX-1", F1, 1)
        self.gate.record_outcome("TX-1", "COMMITTED")
        self.assertEqual(self.gate.route_transfer("TX-1", F1, 1), "DUPLICATE_COMMITTED")
        self.assertEqual(self.gate.ledger_watermark, 1)

    def test_same_id_different_request_fails_closed(self):
        self.gate.route_transfer("TX-1", F1, 1)
        self.assertEqual(self.gate.route_transfer("TX-1", F2, 1), "ID_CONFLICT")

    def test_stale_epoch_fenced_before_new_operation(self):
        self.assertEqual(self.gate.route_transfer("TX-1", F1, 0), "FENCED_STALE_EPOCH")
        self.assertEqual(len(self.gate.operations), 0)

    def test_invalid_operation_id_and_fingerprint_rejected(self):
        for op_id, fingerprint in (("../TX", F1), ("", F1), ("TX", "test"), ("TX", F1.upper())):
            with self.subTest(op_id=op_id, fingerprint=fingerprint):
                with self.assertRaises(ValueError):
                    self.gate.route_transfer(op_id, fingerprint, 1)

    def test_unknown_ack_blocks_cutover_and_duplicate_replay(self):
        self.gate.route_transfer("TX-1", F1, 1)
        self.gate.record_outcome("TX-1", "UNKNOWN")
        self.assertEqual(self.gate.route_transfer("TX-1", F1, 1), "UNKNOWN_REQUIRES_RECONCILIATION")
        self.assertIn("UNRESOLVED_UNKNOWN_COMMANDS", self.gate.assess_cutover("candidate", evidence(self.gate)))
        with self.assertRaises(CutoverBlocked):
            self.gate.rehearse_cutover("candidate", evidence(self.gate))

    def test_unknown_requires_explicit_resolution_observation(self):
        self.gate.route_transfer("TX-1", F1, 1)
        self.gate.record_outcome("TX-1", "UNKNOWN")
        with self.assertRaises(CutoverBlocked):
            self.gate.reconcile_unknown("TX-1", "COMMITTED", evidence_id="")
        with self.assertRaises(CutoverBlocked):
            self.gate.reconcile_unknown("TX-1", "UNKNOWN", evidence_id="synthetic-fixture:test")
        self.gate.reconcile_unknown("TX-1", "COMMITTED", evidence_id="synthetic-fixture:test")
        self.assertEqual(self.gate.ledger_watermark, 1)
        self.assertEqual(self.gate.route_transfer("TX-1", F1, 1), "DUPLICATE_COMMITTED")

    def test_inflight_blocks_transition(self):
        self.gate.route_transfer("TX-1", F1, 1)
        self.assertIn("IN_FLIGHT_COMMANDS", self.gate.assess_cutover("candidate", evidence(self.gate)))

    def test_synthetic_reconciled_cutover_changes_writer_and_fences_old_epoch(self):
        new_epoch = self.gate.rehearse_cutover("candidate", evidence(self.gate))
        self.assertEqual(new_epoch, 2)
        self.assertEqual(self.gate.writer, "candidate")
        self.assertEqual(self.gate.route_transfer("TX-2", F1, 1), "FENCED_STALE_EPOCH")
        self.assertEqual(self.gate.route_transfer("TX-2", F1, 2), "ROUTE_CANDIDATE")
        self.assertEqual(self.gate.todm_g6, "BLOCK")

    def test_existing_id_replay_preserves_legacy_route_after_cutover(self):
        self.gate.route_transfer("TX-1", F1, 1)
        self.gate.record_outcome("TX-1", "COMMITTED")
        self.gate.rehearse_cutover("candidate", evidence(self.gate))
        self.assertEqual(self.gate.route_transfer("TX-1", F1, 2), "DUPLICATE_COMMITTED")
        self.assertEqual(self.gate.operations["TX-1"].writer, "legacy")
        self.assertEqual(self.gate.ledger_watermark, 1)

    def test_rollback_is_blocked_until_new_authority_reconciled(self):
        self.gate.rehearse_cutover("candidate", evidence(self.gate))
        self.gate.route_transfer("TX-1", F1, 2)
        self.gate.record_outcome("TX-1", "UNKNOWN")
        with self.assertRaises(CutoverBlocked):
            self.gate.rehearse_cutover("legacy", evidence(self.gate))
        self.gate.reconcile_unknown("TX-1", "COMMITTED", evidence_id="synthetic-fixture:observed")
        self.assertEqual(self.gate.rehearse_cutover("legacy", evidence(self.gate)), 3)
        self.assertEqual(self.gate.route_transfer("TX-3", F1, 2), "FENCED_STALE_EPOCH")

    def test_balance_watermark_prevents_stale_projection(self):
        self.gate.route_transfer("TX-1", F1, 1)
        self.gate.record_outcome("TX-1", "COMMITTED")
        self.assertEqual(self.gate.read_projection(1), "STALE_PROJECTION")
        self.gate.catch_up_projection(1)
        self.assertEqual(self.gate.read_projection(1), "PROJECTED")
        with self.assertRaises(CutoverBlocked):
            self.gate.catch_up_projection(2)

    def test_all_four_reconciliation_digests_are_required(self):
        for name in ("balances", "operations", "postings", "outbox"):
            with self.subTest(name=name):
                forged = replace(evidence(self.gate), **{f"target_{name}_sha256": sha("different")})
                self.assertIn(name.upper() + "_MISMATCH", self.gate.assess_cutover("candidate", forged))

    def test_watermark_and_counts_must_match(self):
        base = evidence(self.gate)
        for changed in ({"target_watermark": 1}, {"observed_target_count": 1},
                        {"source_inflight_count": 1}, {"source_epoch": 999}):
            with self.subTest(changed=changed):
                self.assertNotEqual(self.gate.assess_cutover("candidate", replace(base, **changed)), ())

    def test_boolean_counts_and_watermarks_are_not_valid_integers(self):
        self.assertIn("INVALID_COUNTS", self.gate.assess_cutover("candidate", replace(evidence(self.gate), source_inflight_count=False)))
        self.assertIn("WATERMARK_MISMATCH", self.gate.assess_cutover("candidate", replace(evidence(self.gate), source_watermark=True)))

    def test_unattributed_report_is_not_cutover_evidence(self):
        report = replace(evidence(self.gate), provenance="production-approved")
        self.assertIn("MISSING_SYNTHETIC_PROVENANCE", self.gate.assess_cutover("candidate", report))

    def test_same_writer_and_nonexistent_writer_refused(self):
        self.assertIn("INVALID_TARGET", self.gate.assess_cutover("legacy", evidence(self.gate)))
        self.assertIn("INVALID_TARGET", self.gate.assess_cutover("unknown", evidence(self.gate)))

    def test_untracked_completion_and_double_completion_rejected(self):
        with self.assertRaises(CutoverBlocked):
            self.gate.record_outcome("missing", "COMMITTED")
        self.gate.route_transfer("TX-1", F1, 1)
        self.gate.record_outcome("TX-1", "COMMITTED")
        with self.assertRaises(CutoverBlocked):
            self.gate.record_outcome("TX-1", "COMMITTED")


if __name__ == "__main__":
    unittest.main()
