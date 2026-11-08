"""Synthetic collector regressions; these are not experiment observations."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import reproduce_campaign as campaign


class CampaignTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.output = self.root / "output"

    def validate(self, experiments=("core",), **kwargs):
        return campaign.validate_request(self.repo, self.output, experiments,
                                         kwargs.get("working", False), kwargs.get("license", False))

    def test_existing_attempt_cannot_be_overwritten(self):
        self.output.mkdir()
        with self.assertRaisesRegex(ValueError, "Output already exists"):
            self.validate()

    def test_e4_requires_core_first(self):
        for experiments in (("e4-prerequisite",), ("e4-prerequisite", "core")):
            with self.subTest(experiments=experiments):
                with self.assertRaisesRegex(ValueError, "core stage earlier"):
                    self.validate(experiments)

    def test_sqlserver_requires_explicit_consent(self):
        with self.assertRaisesRegex(ValueError, "accept-sqlserver-license"):
            self.validate(("e1-sqlserver",))

    def test_duplicate_experiments_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "only once"):
            self.validate(("core", "core"))

    def test_unignored_repository_output_is_rejected(self):
        self.output = self.repo / "new-output"
        with self.assertRaisesRegex(ValueError, "ignored lab/results"):
            self.validate()

    def test_dirty_source_needs_explicit_snapshot_option(self):
        with patch.object(campaign, "git", return_value=b"?? lab/new.py\n"):
            with self.assertRaisesRegex(ValueError, "include-working-tree"):
                self.validate()
            self.assertTrue(self.validate(working=True))

    def test_overlay_copies_new_bytes_and_removes_deleted_files(self):
        checkout = self.root / "checkout"
        checkout.mkdir()
        (self.repo / "new.py").write_text("print('new')\n")
        (checkout / "deleted.py").write_text("old\n")
        campaign.overlay_worktree(self.repo, checkout, ["new.py", "deleted.py"])
        self.assertEqual((checkout / "new.py").read_bytes(), (self.repo / "new.py").read_bytes())
        self.assertFalse((checkout / "deleted.py").exists())

    def test_overlay_rejects_path_escape(self):
        checkout = self.root / "checkout"
        checkout.mkdir()
        (self.root / "outside.txt").write_text("outside")
        with self.assertRaisesRegex(ValueError, "outside the snapshot"):
            campaign.overlay_worktree(self.repo, checkout, ["../outside.txt"])
        self.assertFalse((checkout / "outside.txt").exists())

    def prepare_manifest(self):
        self.output.mkdir()
        artifact = self.output / "raw.json"
        artifact.write_text('{"actual": true}\n')
        campaign.save(self.output / "campaign.json", {
            "status": "FAIL", "artifactSha256": {"raw.json": campaign.sha(artifact)}})
        return artifact

    def test_integrity_does_not_promote_a_failed_run(self):
        self.prepare_manifest()
        verified = campaign.verify_artifacts(self.output)
        self.assertEqual(verified["integrity"], "PASS")
        self.assertEqual(verified["campaignStatus"], "FAIL")

    def test_artifact_tampering_is_rejected(self):
        artifact = self.prepare_manifest()
        artifact.write_text("changed")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            campaign.verify_artifacts(self.output)

    def test_manifest_cannot_read_outside_evidence(self):
        self.prepare_manifest()
        campaign.save(self.output / "campaign.json", {
            "status": "FAIL", "artifactSha256": {"../private": "0" * 64}})
        with self.assertRaisesRegex(ValueError, "leaves the evidence"):
            campaign.verify_artifacts(self.output)

    @unittest.skipUnless(sys.platform == "linux", "Process-session controls require Linux/WSL")
    def test_nonzero_process_retains_stdout_and_stderr(self):
        self.output.mkdir()
        result = campaign.run_command(
            [sys.executable, "-c", "import sys; print('raw'); print('error',file=sys.stderr); sys.exit(7)"],
            self.repo, self.output, "failure", os.environ.copy(), 5)
        self.assertEqual(result["exitCode"], 7)
        self.assertFalse(result["passed"])
        self.assertEqual((self.output / "failure.stdout").read_text(), "raw\n")
        self.assertEqual((self.output / "failure.stderr").read_text(), "error\n")

    @unittest.skipUnless(sys.platform == "linux", "Process-session controls require Linux/WSL")
    def test_timeout_remains_failure_even_when_term_handler_exits_zero(self):
        self.output.mkdir()
        result = campaign.run_command(
            ["bash", "-c", "trap 'echo terminated; exit 0' TERM; echo started; sleep 20"],
            self.repo, self.output, "timeout", os.environ.copy(), 0.1)
        self.assertTrue(result["timedOut"])
        self.assertEqual(result["exitCode"], 0)
        self.assertFalse(result["passed"])
        self.assertIn("terminated", (self.output / "timeout.stdout").read_text())


if __name__ == "__main__":
    unittest.main()
