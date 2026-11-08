"""Focused deterministic regression tests; integration is test_e3.py --profile smoke."""
import json
import os
import shutil
import uuid
from pathlib import Path
import time
import unittest
from unittest.mock import patch

import test_e3 as harness


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((Path(__file__).with_name("workload.json")).read_text())
        self.profile = self.config["profiles"]["smoke"]
        self.offers = harness.make_offers(self.profile, "a" * 32)

    def test_fixed_schedule_unique_identities_and_routes(self):
        self.assertEqual(len(self.offers), 120)
        self.assertEqual(len({r["operationId"] for r in self.offers}), 120)
        self.assertEqual(self.offers[20]["scheduledSeconds"], 2)
        self.assertEqual(self.offers[60]["scheduledSeconds"], 4)
        self.assertEqual([r["replica"] for r in self.offers[:4]], [0, 1, 0, 1])
        self.assertTrue(all(a["scheduledSeconds"] < b["scheduledSeconds"]
                            for a, b in zip(self.offers, self.offers[1:])))

    def test_workload_rejects_unbounded_rate_and_invalid_fault_window(self):
        harness.validate_workload(self.config, self.profile)
        for changed in ({**self.profile, "ratesPerSecond": [100000]},
                        {**self.profile, "restartAtSeconds": 100}):
            with self.assertRaises(ValueError):
                harness.validate_workload(self.config, changed)

    def test_full_generator_drops_instead_of_waiting(self):
        self.assertEqual(harness.dispatch_decision(0, 32, self.config), "MISSED_INFLIGHT_LIMIT")
        self.assertEqual(harness.dispatch_decision(.101, 0, self.config), "MISSED_SCHEDULE")
        self.assertIsNone(harness.dispatch_decision(.05, 0, self.config))

    def test_late_worker_does_not_send(self):
        record = self.offers[0]
        with patch.object(harness, "request_json") as request:
            harness.send_offer(record, 12345, time.monotonic() - 1, self.config)
        request.assert_not_called()
        self.assertEqual(record["outcome"], "MISSED_SCHEDULE")
        self.assertIsNone(record["endToEndMs"])

    def test_latency_includes_dispatch_delay(self):
        record = self.offers[0]
        reply = {"operationId": record["operationId"], "amountCents": 1, "status": "COMMITTED"}
        with patch.object(harness, "request_json", return_value=reply), patch.object(
                harness.time, "monotonic", side_effect=[100.05, 100.08]):
            harness.send_offer(record, 12345, 100, self.config)
        self.assertAlmostEqual(record["endToEndMs"], 80)
        self.assertAlmostEqual(record["dispatchLatenessMs"], 50)

    def test_timeout_is_ambiguous_and_persisted_commit_is_reconciled(self):
        record = self.offers[0]
        with patch.object(harness, "request_json", side_effect=TimeoutError), patch.object(
                harness.time, "monotonic", side_effect=[100, 102]):
            harness.send_offer(record, 12345, 100, self.config)
        self.assertEqual(record["outcome"], "AMBIGUOUS_TRANSPORT")
        result = harness.reconcile([record], [(record["operationId"], 1, 2, 1, "COMMITTED")])
        self.assertTrue(result["consistent"])
        self.assertEqual(result["unacknowledgedPersistedCommits"], 1)

    def test_reconciliation_catches_missing_ack_and_wrong_payload(self):
        record = self.offers[0]
        record["outcome"] = "ACK_COMMITTED"
        self.assertFalse(harness.reconcile([record], [])["consistent"])
        self.assertFalse(harness.reconcile([record], [(record["operationId"], 2, 1, 1, "COMMITTED")])["consistent"])

    def test_reconciliation_rejects_unoffered_and_missed_commits(self):
        record = self.offers[0]
        self.assertFalse(harness.reconcile([record], [(record["operationId"], 1, 2, 1, "COMMITTED")])["consistent"])
        self.assertFalse(harness.reconcile([], [("unknown", 1, 2, 1, "COMMITTED")])["consistent"])

    def test_fixture_guard_rejects_remote_mismatch_and_admin_database(self):
        attested = {"host": "127.0.0.1", "port": 5432, "database": "experiment", "username": "postgres"}
        good = "host=127.0.0.1 port=5432 dbname=experiment user=postgres"
        with patch.dict(os.environ, {"E3_DISPOSABLE_FIXTURE": "YES"}):
            self.assertEqual(harness.validate_dsn(good, attested), attested)
            for bad in (good.replace("127.0.0.1", "example.com"), good.replace("experiment", "postgres"),
                        good + " options='-c search_path=public'", good + " hostaddr=1.2.3.4",
                        good.replace("5432", "5433")):
                with self.assertRaises(ValueError):
                    harness.validate_dsn(bad, attested)
        with patch.dict(os.environ, {"E3_DISPOSABLE_FIXTURE": "NO"}):
            with self.assertRaises(ValueError):
                harness.validate_dsn(good, attested)

    def test_malformed_response_preserves_offer_as_ambiguous(self):
        record = self.offers[0]
        with patch.object(harness, "request_json", return_value=[]), patch.object(
                harness.time, "monotonic", side_effect=[100, 100.01]):
            harness.send_offer(record, 12345, 100, self.config)
        self.assertEqual(record["outcome"], "AMBIGUOUS_TRANSPORT")
        self.assertIsNotNone(record["completionSeconds"])

    def test_exported_workspace_does_not_require_git_executable(self):
        with patch.dict(os.environ, {"SOURCE_HEAD_SHA": "a" * 40,
                                    "SOURCE_ARCHIVE_SHA256": "b" * 64,
                                    "SOURCE_WORKTREE_DIRTY": "true"}), patch.object(
                harness.subprocess, "run", side_effect=FileNotFoundError):
            provenance = harness.source_provenance()
        self.assertIsNone(provenance["localGitHead"])
        self.assertEqual(len(provenance["sourceSetSha256"]), 64)
        self.assertEqual(provenance["launcherAttestedExport"]["SOURCE_WORKTREE_DIRTY"], "true")

    def runtime_fixture(self):
        root = harness.HERE / "results" / ("retention-test-" + uuid.uuid4().hex)
        build, output = root / "build", root / "output"
        build.mkdir(parents=True)
        output.mkdir()
        self.addCleanup(shutil.rmtree, root)
        return build, output

    def test_runtime_retention_preserves_bytes_and_flat_manifest_names(self):
        build, output = self.runtime_fixture()
        for name, data in {"E3Fixture.dll": b"original dll bytes", "E3Fixture.deps.json": b"{}"}.items():
            (build / name).write_bytes(data)
        (build / "ignored.pdb").write_bytes(b"not a runtime artifact")
        hashes = harness.retain_runtime_artifacts(build, output)
        self.assertEqual(set(hashes), {"E3Fixture.dll", "E3Fixture.deps.json"})
        for name, sha in hashes.items():
            self.assertEqual((output / name).read_bytes(), (build / name).read_bytes())
            self.assertEqual(harness.digest(output / name), sha)
        self.assertEqual(hashes, {p.name: harness.digest(p) for p in output.iterdir()})

    def test_runtime_retention_never_overwrites_existing_artifact(self):
        build, output = self.runtime_fixture()
        (build / "E3Fixture.dll").write_bytes(b"source")
        (output / "E3Fixture.dll").write_bytes(b"existing")
        with self.assertRaises(ValueError):
            harness.retain_runtime_artifacts(build, output)
        self.assertEqual((output / "E3Fixture.dll").read_bytes(), b"existing")

    def test_runtime_retention_rejects_directories_and_symlinks(self):
        build, output = self.runtime_fixture()
        (build / "directory.dll").mkdir()
        with self.assertRaises(ValueError):
            harness.retain_runtime_artifacts(build, output)
        (build / "directory.dll").rmdir()
        (build / "file.dll").write_bytes(b"original")
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaises(ValueError):
                harness.retain_runtime_artifacts(build, output)
        self.assertEqual(list(output.iterdir()), [])

    def test_runtime_retention_bounds_count_and_location(self):
        build, output = self.runtime_fixture()
        for i in range(129):
            (build / f"file{i}.dll").write_bytes(b"")
        with self.assertRaises(ValueError):
            harness.retain_runtime_artifacts(build, output)
        with self.assertRaises(ValueError):
            harness.retain_runtime_artifacts(harness.ROOT.parent, output)
        self.assertEqual(list(output.iterdir()), [])

    def test_runtime_retention_rejects_oversized_file_before_copy(self):
        build, output = self.runtime_fixture()
        source = build / "large.dll"
        source.write_bytes(b"small test payload")
        original_stat = Path.stat
        def fake_stat(path, *args, **kwargs):
            result = original_stat(path, *args, **kwargs)
            if path == source:
                values = list(result)
                values[6] = 129 * 1024 * 1024
                return os.stat_result(values)
            return result
        with patch.object(Path, "stat", fake_stat):
            with self.assertRaises(ValueError):
                harness.retain_runtime_artifacts(build, output)
        self.assertEqual(list(output.iterdir()), [])

    def test_empty_percentile_is_not_zero(self):
        self.assertIsNone(harness.percentile([], .99))
        self.assertEqual(harness.percentile([1, 5, 3], .99), 5)


if __name__ == "__main__":
    unittest.main()
