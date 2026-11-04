"""Adversarial oracle tests for functional-first, brownfield extraction waves."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from wave_gate import WaveError, assess

HERE = Path(__file__).resolve().parent


def source():
    return json.loads((HERE / "functional_capabilities.json").read_text(encoding="utf-8"))


def waves():
    return json.loads((HERE / "wave_fixture.json").read_text(encoding="utf-8"))


class FunctionalWaveTests(unittest.TestCase):
    def test_reference_fixture_refutes_unsafe_transfer_and_batch(self):
        report = assess(source(), waves())
        self.assertEqual(report["catalogTotal"], 30)
        self.assertEqual(report["catalogNeedsEvidence"], 30)
        self.assertEqual(report["structuralCandidates"], 2)
        self.assertEqual(report["rejected"], 2)
        by_id = {x["id"]: x for x in report["proposals"]}
        self.assertEqual(by_id["W01"]["structuralDecision"], "CANDIDATE_ONLY")
        self.assertEqual(by_id["W04"]["structuralDecision"], "CANDIDATE_ONLY")
        self.assertIn("SPLIT_ATOMIC_LEDGER_BOUNDARY", by_id["W02"]["blockers"])
        self.assertIn("SPLIT_BATCH_CUTOFF_OR_RESTART", by_id["W03"]["blockers"])
        self.assertIn("UNRESOLVED_RUNTIME_DEPENDENCY", by_id["W03"]["blockers"])
        self.assertEqual(report["automaticApprovedWaves"], 0)
        self.assertEqual(report["todmG6"], "BLOCK")
        self.assertFalse(report["deploymentAuthorized"])

    def test_watermark_and_fallback_are_required(self):
        for key in ("watermarkRequired", "sourceFallbackRequired", "nonAuthoritative",
                    "noExternalEffects", "idempotentRebuild"):
            with self.subTest(key=key):
                candidate = waves()
                candidate["waves"][0]["readContract"][key] = False
                report = assess(source(), candidate)["proposals"][0]
                self.assertIn("UNSAFE_NONAUTHORITATIVE_READ_CONTRACT", report["blockers"])

    def test_read_projection_cannot_take_financial_authority(self):
        candidate = waves()
        candidate["waves"][0]["sourceAuthority"] = "CANDIDATE"
        candidate["waves"][0]["writesAllowed"] = True
        self.assertEqual(assess(source(), candidate)["proposals"][0]["structuralDecision"], "REJECT")

    def test_atomic_unit_cannot_be_split_by_one_service_per_program(self):
        candidate = waves()
        candidate["waves"][1]["capabilities"] = ["CAP-019"]
        self.assertIn("SPLIT_ATOMIC_LEDGER_BOUNDARY",
                      assess(source(), candidate)["proposals"][1]["blockers"])

    def test_external_effect_crossing_blocks_command(self):
        candidate = waves()
        candidate["waves"][1]["capabilities"] = ["CAP-011"]
        row = assess(source(), candidate)["proposals"][1]
        self.assertIn("UNRECONCILED_EXTERNAL_EFFECT", row["blockers"])

    def test_retire_cannot_suppress_seasonal_dependency(self):
        candidate = waves()
        candidate["waves"][2]["capabilities"] = ["CAP-022"]
        row = assess(source(), candidate)["proposals"][2]
        self.assertIn("UNRESOLVED_RUNTIME_DEPENDENCY", row["blockers"])
        self.assertIn("RETIRE_HAS_DECLARED_CONSUMERS", row["blockers"])

    def test_fake_complete_catalog_still_no_auto_approval(self):
        catalog = source()
        # Fake metadata is syntactically possible but can never approve a wave.
        for cap in catalog["capabilities"]:
            cap["status"] = "OWNER_REVIEWED"
            cap["owner"] = "synthetic-reviewer"
            cap["unknowns"] = []
            cap["approval"] = {"reviewer": "synthetic-reviewer",
                               "decisionRef": "synthetic-only",
                               "reviewedAt": "2026-11-04"}
            cap["sources"] = [{
                "kind": "approved-policy", "reference": "synthetic-only",
                "observedAt": "2026-11-04", "sha256": "a" * 64,
                "approvedForUse": True
            }]
        report = assess(catalog, waves())
        self.assertEqual(report["catalogNeedsEvidence"], 0)
        self.assertEqual(report["automaticApprovedWaves"], 0)
        self.assertEqual(report["todmG2"], "INCONCLUSIVE")
        self.assertEqual(report["todmG6"], "BLOCK")

    def test_missing_or_dangling_dependency_rejected_as_bad_input(self):
        for value in ("CAP-999", "CAP-007"):
            with self.subTest(value=value):
                candidate = waves()
                candidate["dependencies"][0]["source"] = value
                with self.assertRaises(WaveError):
                    assess(source(), candidate)

    def test_duplicate_dependency_refused(self):
        candidate = waves()
        candidate["dependencies"].append(copy.deepcopy(candidate["dependencies"][0]))
        with self.assertRaises(WaveError):
            assess(source(), candidate)

    def test_reject_unapproved_input_classification(self):
        candidate = waves()
        candidate["classification"] = "APPROVED_PRODUCTION_MIGRATION"
        with self.assertRaises(WaveError):
            assess(source(), candidate)

    def test_no_hidden_approval_override(self):
        candidate = waves()
        candidate["waves"][0]["todmG6"] = "PASS"
        with self.assertRaises(WaveError):
            assess(source(), candidate)

    def test_predecessor_must_exist_and_precede_wave(self):
        candidate = waves()
        candidate["waves"][0]["predecessors"] = ["W02"]
        with self.assertRaises(WaveError):
            assess(source(), candidate)
        candidate["waves"][0]["predecessors"] = ["W999"]
        with self.assertRaises(WaveError):
            assess(source(), candidate)

    def test_duplicate_wave_sequence_rejected(self):
        candidate = waves()
        candidate["waves"][1]["sequence"] = 1
        with self.assertRaises(WaveError):
            assess(source(), candidate)

    def test_extra_unknown_relations_fail_closed(self):
        candidate = waves()
        candidate["dependencies"][0]["relation"] = "unproven-sql"
        with self.assertRaises(WaveError):
            assess(source(), candidate)

    def test_no_empty_or_doubled_capability_set(self):
        for selected in ([], ["CAP-005", "CAP-005"], ["CAP-999"]):
            with self.subTest(selected=selected):
                candidate = waves()
                candidate["waves"][0]["capabilities"] = selected
                with self.assertRaises(WaveError):
                    assess(source(), candidate)


if __name__ == "__main__":
    unittest.main()
