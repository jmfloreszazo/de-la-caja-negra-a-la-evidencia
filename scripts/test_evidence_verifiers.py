"""Focused offline regression tests for evidence verification (including python -O)."""
import ast
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "evidence"


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.folder = ROOT / (".verifier-tests-" + uuid.uuid4().hex)
        self.folder.mkdir()
        self.addCleanup(shutil.rmtree, self.folder)

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_invalid_campaigns_fail_even_with_optimization(self):
        campaign = self.folder / "campaign"
        run = campaign / "runs" / "e1-azure-20261108-01"
        self.write_json(run / "request.json", {"sourceSha256": "wrong"})
        self.write_json(campaign / "runs" / "e1-azure-20261108-01-evidence" / "completion.json",
                        {"sourceSha256": "different"})
        raw = campaign / "todm-azure-02-evidence"
        self.write_json(raw / "validation.json", {"evaluationVerdict": "FAIL", "releaseOutcome": "BLOCK"})
        self.write_json(raw / "qualification" / "qualification.json", {})
        for script in ("verify_azure_e1_e4.py", "summarize_todm_azure.py"):
            for flags in ([], ["-O"]):
                with self.subTest(script=script, flags=flags):
                    result = subprocess.run([sys.executable, *flags, str(SCRIPTS / script),
                                             "--campaign", str(campaign)], capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Verification failed:", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_campaign_checks_do_not_use_assert(self):
        for path in SCRIPTS.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            self.assertFalse(any(isinstance(node, ast.Assert) for node in ast.walk(tree)), path)

    def test_summary_is_read_only_semantic_and_explicit_create_only(self):
        checks = module("_checks")
        path = self.folder / "summary.json"
        with self.assertRaisesRegex(SystemExit, "summary missing"):
            checks.compare_summary(path, {"value": 1})
        self.assertFalse(path.exists())
        checks.compare_summary(path, {"value": 1}, write_summary=True)
        path.write_bytes(b'{ "value": 1 }\r\n')
        before = path.read_bytes()
        checks.compare_summary(path, {"value": 1})
        self.assertEqual(path.read_bytes(), before)
        with self.assertRaisesRegex(SystemExit, "differs semantically"):
            checks.compare_summary(path, {"value": 2}, write_summary=True)
        self.assertEqual(path.read_bytes(), before)

    def test_manifest_checks_receipts_not_just_regenerated_text(self):
        manifest = module("dist_manifest")
        archive = self.folder / "example.zip"
        archive.write_bytes(b"preserved archive bytes")
        receipt = archive.with_suffix(".receipt.json")
        output = self.folder / "DIST_MANIFEST.md"
        for metadata, expected in (({"sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}, 0),
                                   ({"sha256": "0" * 64}, 1), ({}, 2), (None, 2)):
            with self.subTest(metadata=metadata):
                if metadata is None:
                    receipt.unlink()
                else:
                    self.write_json(receipt, metadata)
                with patch.object(manifest, "DIST", self.folder), patch.object(manifest, "MANIFEST", output):
                    output.write_text(manifest.render(), encoding="utf-8")
                    before = output.read_bytes()
                    with patch.object(sys, "argv", ["dist_manifest.py", "--verify"]), redirect_stdout(io.StringIO()) as log:
                        self.assertEqual(manifest.main(), expected)
                    self.assertEqual(output.read_bytes(), before)
                    if expected:
                        self.assertNotIn("PASS", log.getvalue())
                    if expected == 2:
                        self.assertIn("INCOMPLETE", log.getvalue())
                    output.write_text("stale", encoding="utf-8")
                    with patch.object(sys, "argv", ["dist_manifest.py", "--verify"]), redirect_stdout(io.StringIO()):
                        self.assertNotEqual(manifest.main(), 0)

    def test_unknown_and_crossed_status_kinds_fail(self):
        wrapper = '''
import json, runpy, sys
from pathlib import Path
original = Path.read_text
status, kind = sys.argv[2:4]
claims_path = Path(sys.argv[1]) / "evidence" / "claims.json"
def read(path, *args, **kwargs):
    text = original(path, *args, **kwargs)
    if path == claims_path:
        data = json.loads(text)
        claim = next(item for item in data["claims"] if item["status"] == status)
        claim["evidence"] = {"kind": kind, "run_id": 123, "assets": ["a", "b", "c", "d"]}
        return json.dumps(data)
    return text
Path.read_text = read
target = str(Path(sys.argv[1]) / "scripts" / "check_evidence.py")
sys.argv = [target]
runpy.run_path(target, run_name="__main__")
'''
        for status, kind in (("ci_verified", "unknown"), ("published", "unknown"),
                             ("ci_verified", "github_release"), ("published", "github_actions")):
            with self.subTest(status=status, kind=kind):
                result = subprocess.run([sys.executable, "-O", "-c", wrapper, str(ROOT), status, kind],
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("requires evidence kind", result.stdout)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
