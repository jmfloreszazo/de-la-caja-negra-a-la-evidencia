"""Offline controls, not evidence of live model quality."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import live


class PayloadTests(unittest.TestCase):
    def test_evaluate_cli_selects_engine_and_defaults_to_docker(self):
        base = ["live.py", "evaluate", "--attempt", "retained", "--legacy-results", "legacy"]
        for extra, expected in (([], "docker"), (["--engine", "podman"], "podman")):
            with patch("sys.argv", base + extra), patch.object(live, "evaluate") as evaluate:
                live.main()
            self.assertEqual(evaluate.call_args.args[0].engine, expected)

    def test_evaluate_uses_selected_engine_without_model_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            attempt, legacy = root / "attempt", root / "legacy"
            attempt.mkdir()
            legacy.mkdir()
            live.save(attempt / "candidate.json", {"program": "return 0;", "tests": [
                {"input": "", "expected": "INVALID|00000000"}]})
            for name in ("summary.json", "none-observations.json"):
                live.save(legacy / name, {})
            args = SimpleNamespace(attempt=attempt, legacy_results=legacy, output=root / "out", engine="podman")
            with patch.object(live.platform, "system", return_value="Linux"), \
                    patch.object(live.os, "getuid", return_value=1000, create=True), \
                    patch.object(live.os, "getgid", return_value=1000, create=True), \
                    patch.object(live, "source_provenance", return_value={"sourceProvenance": "test"}), \
                    patch.object(live, "read_legacy", return_value={}), \
                    patch.object(live, "Containers") as containers, \
                    patch.object(live, "request") as request:
                containers.return_value.command.side_effect = RuntimeError("stop before execution")
                containers.return_value.commands = []
                with self.assertRaisesRegex(RuntimeError, "stop before execution"):
                    live.evaluate(args)
            containers.assert_called_once_with("podman", live.DEFAULT_IMAGE, args.output)
            request.assert_not_called()
            report = live.load(args.output / "evaluation.json")
            self.assertEqual(report["host"]["containerEngine"], "podman")
            self.assertEqual(report["host"]["executionLocation"], "unverified")
            self.assertEqual(report["status"], "FAILED")
            self.assertTrue(report["protectedUnchanged"])

    def test_valid_payload(self):
        payload = {"program": "return 0;", "tests": [{"input": "", "expected": "INVALID|00000000"}]}
        self.assertEqual(live.candidate_payload(json.dumps(payload)), payload)

    def test_invalid_payloads(self):
        for value in ([], {}, {"program": "", "tests": []},
                      {"program": "x", "tests": [{"input": "a\nb", "expected": "INVALID|00000000"}]},
                      {"program": "x", "tests": [{"input": "a", "expected": "PASS"}]},
                      {"program": "x", "tests": [{"input": "", "expected": "INVALID|00000000", "path": "/x"}]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                live.candidate_payload(json.dumps(value))

    def test_resource_limits(self):
        test = {"input": "", "expected": "INVALID|00000000"}
        for program, tests in (("x" * 32001, [test]), ("x", [test] * 65)):
            with self.assertRaises(ValueError):
                live.candidate_payload(json.dumps({"program": program, "tests": tests}))

    def test_endpoint_constraints(self):
        for endpoint in ("http://test.openai.azure.com", "https://evil.example",
                         "https://test.openai.azure.com.evil.example", "https://u:p@test.openai.azure.com",
                         "https://test.openai.azure.com/path", "https://test.openai.azure.com?secret=x"):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                live.endpoint_url(endpoint)
        self.assertEqual(live.endpoint_url("https://test.openai.azure.com/"),
                         "https://test.openai.azure.com/openai/v1/chat/completions")

    def test_redirect_is_never_followed(self):
        with self.assertRaisesRegex(ValueError, "redirects"):
            live.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example")

    def test_request_budget_prevents_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path(directory) / "previous"
            previous.mkdir()
            (previous / "evaluation").mkdir()
            live.save(previous / "request.json", {
                "attempt": 3, "endpoint": live.endpoint_url("https://test.openai.azure.com"),
                "body": {"model": "test", "messages": []}})
            live.save(previous / "response.json", {"choices": [{"message": {"content": "{}"}}]})
            live.save(previous / "evaluation/self-feedback.json", {"status": "FAIL"})
            args = SimpleNamespace(previous=previous, output=Path(directory) / "next",
                                   endpoint="https://test.openai.azure.com", model="test", subscription="test-subscription")
            with patch.object(live.subprocess, "run") as process:
                with self.assertRaisesRegex(ValueError, "budget exhausted"):
                    live.request(args)
            process.assert_not_called()
            self.assertFalse(args.output.exists())

    def test_repair_does_not_send_independent_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path(directory) / "previous"
            previous.mkdir()
            (previous / "evaluation").mkdir()
            live.save(previous / "request.json", {
                "attempt": 1, "endpoint": live.endpoint_url("https://test.openai.azure.com"),
                "body": {"model": "test", "messages": [{"role": "user", "content": live.PROMPT}]}})
            live.save(previous / "response.json", {"choices": [{"message": {"content": "{}"}}]})
            live.save(previous / "evaluation/self-feedback.json", {"status": "FAIL"})
            live.save(previous / "evaluation/evaluation.json", {"secret": "HIDDEN_ORACLE"})
            args = SimpleNamespace(previous=previous, output=Path(directory) / "next",
                                   endpoint="https://test.openai.azure.com", model="test", subscription="test-subscription")
            with patch.object(live.shutil, "which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "Azure CLI"):
                    live.request(args)
            request = live.load(args.output / "request.json")
            self.assertNotIn("HIDDEN_ORACLE", json.dumps(request))
            self.assertEqual(request["attempt"], 2)


if __name__ == "__main__":
    unittest.main()
