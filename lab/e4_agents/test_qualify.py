"""Regression controls; synthetic fixtures here are not experimental evidence."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import qualify


class LegacyEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name)
        self.cases = json.loads((qualify.LAB / "contracts/cases.json").read_text())
        self.summary = {
            "status": "PASS",
            "baselineSha256": qualify.sha(qualify.LAB / "contracts/cases.json"),
            "sourceSha256": {
                name: qualify.sha(qualify.LAB / name)
                for name in ("legacy/fee.cob", "Gate/Program.cs", "Candidate/Program.cs")
            },
        }
        self.rows = [{"id": case["id"], "legacy": case["expected"]} for case in self.cases]

    def read(self):
        (self.output / "summary.json").write_text(json.dumps(self.summary))
        (self.output / "none-observations.json").write_text(json.dumps(self.rows))
        return qualify.read_legacy(self.output, self.cases)

    def test_matching_evidence_is_preserved(self):
        self.assertEqual(self.read(), {row["id"]: row["legacy"] for row in self.rows})

    def test_failed_legacy_run_is_rejected(self):
        self.summary["status"] = "FAIL"
        with self.assertRaisesRegex(ValueError, "successful run"):
            self.read()

    def test_stale_contract_is_rejected(self):
        self.summary["baselineSha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "current frozen contract"):
            self.read()

    def test_each_stale_source_is_rejected(self):
        original = copy.deepcopy(self.summary)
        for name in original["sourceSha256"]:
            with self.subTest(source=name):
                self.summary = copy.deepcopy(original)
                self.summary["sourceSha256"][name] = "0" * 64
                with self.assertRaisesRegex(ValueError, "source differs"):
                    self.read()

    def test_missing_unknown_and_duplicate_cases_are_rejected(self):
        original = copy.deepcopy(self.rows)
        unknown = copy.deepcopy(original)
        unknown[0]["id"] = "UNKNOWN"
        for rows in (original[:-1], [original[0], *original[:-1]], unknown):
            with self.subTest(rows=rows[:2]):
                self.rows = rows
                with self.assertRaisesRegex(ValueError, "missing, unknown or duplicate"):
                    self.read()

    def test_incorrect_legacy_value_is_rejected(self):
        self.rows[0]["legacy"] += "incorrect"
        with self.assertRaisesRegex(ValueError, "does not satisfy"):
            self.read()


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.enterContext(patch.object(qualify, "LAB", self.root / "lab"))
        self.enterContext(patch.dict(os.environ, {}, clear=True))
        self.metadata = {"SOURCE_HEAD_SHA": "a" * 40,
                         "SOURCE_ARCHIVE_SHA256": "b" * 64,
                         "SOURCE_WORKTREE_DIRTY": "true"}

    def test_export_requires_complete_valid_attestation(self):
        with self.assertRaisesRegex(ValueError, "requires all three"):
            qualify.source_provenance()
        for name, invalid in (("SOURCE_HEAD_SHA", "main"), ("SOURCE_ARCHIVE_SHA256", "unknown"),
                              ("SOURCE_WORKTREE_DIRTY", "maybe"), ("SOURCE_WORKTREE_DIRTY", "")):
            metadata = {**self.metadata, name: invalid}
            with patch.dict(os.environ, metadata), self.assertRaises(ValueError):
                qualify.source_provenance()
        for missing in self.metadata:
            metadata = {key: value for key, value in self.metadata.items() if key != missing}
            with patch.dict(os.environ, metadata), self.assertRaisesRegex(ValueError, "together"):
                qualify.source_provenance()

    def test_export_records_attestation_not_cloud_or_verified_archive(self):
        for dirty, expected in (("true", True), ("1", True), ("false", False), ("0", False)):
            with patch.dict(os.environ, {**self.metadata, "SOURCE_WORKTREE_DIRTY": dirty}), \
                    patch.object(qualify.subprocess, "check_output") as git:
                provenance = qualify.source_provenance()
            git.assert_not_called()
            self.assertEqual(provenance["sourceCommit"], "a" * 40)
            self.assertEqual(provenance["sourceArchiveSha256"], "b" * 64)
            self.assertEqual(provenance["worktreeDirty"], expected)
            self.assertEqual(provenance["sourceProvenance"], "launcher-attested-export")
            self.assertFalse(provenance["sourceArchiveVerifiedByEvaluator"])
            self.assertNotIn("Azure", json.dumps(provenance))

    def test_git_fallback_and_conflicting_attestation(self):
        (self.root / ".git").mkdir()
        with patch.object(qualify.subprocess, "check_output", side_effect=["a" * 40 + "\n", " M file\n"]):
            provenance = qualify.source_provenance()
        self.assertEqual(provenance["sourceProvenance"], "local-git")
        self.assertTrue(provenance["worktreeDirty"])
        with patch.dict(os.environ, self.metadata), \
                patch.object(qualify.subprocess, "check_output", side_effect=["c" * 40 + "\n", " M file\n"]):
            with self.assertRaisesRegex(ValueError, "conflicts"):
                qualify.source_provenance()

    def test_host_is_observed_not_inferred_from_environment(self):
        with patch.dict(os.environ, {**self.metadata, "AZURE_VM_NAME": "claimed-cloud"}), \
                patch.object(os, "getuid", return_value=1000, create=True), \
                patch.object(os, "getgid", return_value=1001, create=True):
            host = qualify.host_provenance("podman")
        self.assertEqual(host["node"], qualify.platform.node())
        self.assertEqual(host["release"], qualify.platform.release())
        self.assertEqual(host["uid"], 1000)
        self.assertEqual(host["gid"], 1001)
        self.assertEqual(host["executionLocation"], "unverified")


class ContainerPolicyTests(unittest.TestCase):
    identifier = "a" * 64

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name)
        self.runner = qualify.Containers("docker", "test-image", self.output)
        for name in ("getuid", "getgid"):
            self.enterContext(patch.object(os, name, return_value=1000, create=True))
        self.mounts = [(self.output, "/candidate", True)]
        self.state = {
            "Config": {"User": "1000:1000"},
            "HostConfig": {
                "ReadonlyRootfs": True, "NetworkMode": "none", "Privileged": False,
                "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges"],
                "Memory": 1_073_741_824, "NanoCpus": 1_000_000_000,
                "PidsLimit": 128, "PidMode": "",
            },
            "Mounts": [{"Type": "bind", "Destination": "/candidate", "RW": True,
                        "Source": str(self.output.resolve())}],
            "State": {"Running": False, "ExitCode": 0},
        }

    @staticmethod
    def result(stdout="", code=0):
        return subprocess.CompletedProcess([], code, stdout, "")

    def inspected(self):
        return self.result(json.dumps([self.state]))

    def test_policy_is_checked_before_start_and_owned_id_is_removed(self):
        with patch.object(self.runner, "command", side_effect=[
            self.result(self.identifier), self.inspected(), self.result("actual output"),
            self.inspected(), self.result(),
        ]) as command:
            self.assertEqual(self.runner.run("good", self.mounts, ["true"]), "actual output")
        calls = [call.args[0] for call in command.call_args_list]
        self.assertEqual([call[0] for call in calls], ["create", "inspect", "start", "inspect", "rm"])
        self.assertEqual(calls[-1], ["rm", "-f", self.identifier])

    def test_unsafe_policy_prevents_start_and_still_removes_container(self):
        original = copy.deepcopy(self.state)
        invalid = {
            "ReadonlyRootfs": False, "NetworkMode": "bridge", "Privileged": True,
            "CapDrop": [], "SecurityOpt": [], "Memory": 0, "NanoCpus": 0,
            "PidsLimit": 0, "PidMode": "host",
        }
        for key, value in invalid.items():
            with self.subTest(setting=key):
                self.state = copy.deepcopy(original)
                self.state["HostConfig"][key] = value
                with patch.object(self.runner, "command", side_effect=[
                    self.result(self.identifier), self.inspected(), self.result(),
                ]) as command:
                    with self.assertRaisesRegex(RuntimeError, "isolation configuration"):
                        self.runner.run("unsafe", self.mounts, ["true"])
                self.assertEqual([call.args[0][0] for call in command.call_args_list],
                                 ["create", "inspect", "rm"])

    def test_wrong_user_and_mount_permissions_are_rejected(self):
        original = copy.deepcopy(self.state)
        for setting in ("user", "readonly", "extra", "source", "volume", "duplicate"):
            with self.subTest(setting=setting):
                self.state = copy.deepcopy(original)
                if setting == "user":
                    self.state["Config"]["User"] = "0:0"
                elif setting == "readonly":
                    self.state["Mounts"][0]["RW"] = False
                elif setting == "source":
                    self.state["Mounts"][0]["Source"] = "/credentials"
                elif setting == "volume":
                    self.state["Mounts"].append({"Type": "volume", "Destination": "/credentials"})
                elif setting == "duplicate":
                    self.state["Mounts"].append(copy.deepcopy(self.state["Mounts"][0]))
                else:
                    self.state["Mounts"].append(
                        {"Type": "bind", "Destination": "/credentials", "RW": False})
                with patch.object(self.runner, "command", return_value=self.inspected()):
                    with self.assertRaisesRegex(RuntimeError, "isolation configuration"):
                        self.runner.inspect_policy(self.identifier, "unsafe", self.mounts)

    def test_podman_expanded_capabilities_and_keep_id(self):
        self.runner.engine = "podman"
        self.state["HostConfig"].update(CapDrop=["CAP_CHOWN", "CAP_SETUID"],
                                        UsernsMode="private", NanoCpus=0,
                                        CpuPeriod=100000, CpuQuota=100000)
        for empty in ([], None):
            self.state.update(EffectiveCaps=empty, BoundingCaps=empty)
            with self.subTest(empty=empty), patch.object(self.runner, "command", side_effect=[
                self.result(self.identifier), self.inspected(), self.result("actual output"),
                self.inspected(), self.result(),
            ]) as command:
                self.assertEqual(self.runner.run("podman", self.mounts, ["true"]), "actual output")
                create = command.call_args_list[0].args[0]
                self.assertEqual(create[create.index("--userns") + 1], "keep-id")
                self.assertIn("--read-only-tmpfs=false", create)
                self.assertIn("--http-proxy=false", create)
                self.assertIn("--network", create)
                self.assertNotIn("--privileged", create)

    def test_podman_unknown_or_remaining_capabilities_fail_closed(self):
        self.runner.engine = "podman"
        self.state["HostConfig"]["UsernsMode"] = "private"
        self.state.update(EffectiveCaps=[], BoundingCaps=[])
        original = copy.deepcopy(self.state)
        for key in ("EffectiveCaps", "BoundingCaps"):
            for value in ("missing", ["CAP_NET_ADMIN"], "", False):
                with self.subTest(key=key, value=value):
                    self.state = copy.deepcopy(original)
                    if value == "missing":
                        del self.state[key]
                    else:
                        self.state[key] = value
                    with patch.object(self.runner, "command", return_value=self.inspected()):
                        with self.assertRaisesRegex(RuntimeError, "isolation configuration"):
                            self.runner.inspect_policy(self.identifier, "unsafe", self.mounts)
        for key, value in (("UsernsMode", "host"), ("CapAdd", ["CAP_CHOWN"])):
            self.state = copy.deepcopy(original)
            self.state["HostConfig"][key] = value
            with patch.object(self.runner, "command", return_value=self.inspected()):
                with self.assertRaisesRegex(RuntimeError, "isolation configuration"):
                    self.runner.inspect_policy(self.identifier, "unsafe", self.mounts)

    def test_engine_names_are_restricted(self):
        with self.assertRaisesRegex(ValueError, "docker or podman"):
            qualify.Containers("unknown", "image", self.output)

    def test_expected_gate_failure_is_not_an_engine_failure(self):
        self.state["State"]["ExitCode"] = 2
        for code in (0, 2):
            with self.subTest(engine_exit=code):
                with patch.object(self.runner, "command", side_effect=[
                    self.result(self.identifier), self.inspected(), self.result("FAIL", code),
                    self.inspected(), self.result(),
                ]):
                    self.assertEqual(self.runner.run("mutant", self.mounts, ["gate"],
                                                     expected_exit=2), "FAIL")

    def test_unexpected_exit_fails_and_removes_container(self):
        self.state["State"]["ExitCode"] = 137
        with patch.object(self.runner, "command", side_effect=[
            self.result(self.identifier), self.inspected(), self.result("", 137),
            self.inspected(), self.result(),
        ]) as command:
            with self.assertRaisesRegex(RuntimeError, "unexpected container exit"):
                self.runner.run("crash", self.mounts, ["candidate"])
        self.assertEqual(command.call_args.args[0], ["rm", "-f", self.identifier])

    def test_timeout_preserves_partial_logs_and_removes_container(self):
        timeout = subprocess.TimeoutExpired(["docker", "start"], 180,
                                            output=b"partial output", stderr=b"partial error")
        with patch.object(self.runner, "command", side_effect=[
            self.result(self.identifier), self.inspected(), timeout, self.result(),
        ]) as command:
            with self.assertRaises(subprocess.TimeoutExpired):
                self.runner.run("timeout", self.mounts, ["candidate"])
        self.assertEqual(command.call_args.args[0], ["rm", "-f", self.identifier])
        self.assertEqual((self.output / "timeout.stdout").read_text(), "partial output")
        self.assertEqual((self.output / "timeout.stderr").read_text(), "partial error")
        self.assertEqual(json.loads((self.output / "timeout.timeout.json").read_text()),
                         {"timeoutSeconds": 180})

    def test_cleanup_failure_is_reported(self):
        with patch.object(self.runner, "command", side_effect=[
            self.result(self.identifier), self.inspected(), self.result(),
            self.inspected(), self.result(code=1),
        ]):
            with self.assertRaisesRegex(RuntimeError, "Failed to remove owned container"):
                self.runner.run("cleanup", self.mounts, ["true"])


if __name__ == "__main__":
    unittest.main()
