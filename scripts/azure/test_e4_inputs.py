"""Offline replay transport controls; no model invocation or cloud access."""
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("e4_inputs", Path(__file__).with_name("e4-inputs.py"))
inputs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inputs)


class ReplayInputTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.attempt = self.root / "attempt"
        self.legacy = self.root / "legacy"
        self.attempt.mkdir()
        self.legacy.mkdir()
        candidate = {"program": "return 0;", "tests": []}
        values = {
            "attempt/candidate.json": candidate,
            "attempt/request.json": {"status": "RECEIVED", "usage": {"total_tokens": 1}},
            "attempt/response.json": {"choices": [{"message": {"content": json.dumps(candidate)}}],
                                      "usage": {"total_tokens": 1}},
            "legacy/summary.json": {"status": "PASS"},
            "legacy/none-observations.json": [],
        }
        for name, value in values.items():
            (self.root / name).write_text(json.dumps(value))
        self.archive = self.root / "inputs.tar"

    def test_round_trip_is_exact_and_does_not_copy_other_files(self):
        (self.attempt / "private-file.txt").write_text("not an input")
        record = inputs.pack(self.attempt, self.legacy, self.archive)
        self.assertEqual(set(record["files"]), set(inputs.FILES))
        output = self.root / "unpacked"
        inputs.unpack(self.archive, output)
        for name in inputs.FILES:
            self.assertEqual((self.root / name).read_bytes(), (output / name).read_bytes())
        self.assertFalse((output / "attempt/private-file.txt").exists())

    def test_changed_candidate_cannot_be_exported_as_original_response(self):
        (self.attempt / "candidate.json").write_text('{"program":"changed"}')
        with self.assertRaisesRegex(ValueError, "differs"):
            inputs.pack(self.attempt, self.legacy, self.archive)
        self.assertFalse(self.archive.exists())

    def test_usage_mismatch_is_rejected(self):
        (self.attempt / "request.json").write_text('{"status":"RECEIVED","usage":{}}')
        with self.assertRaisesRegex(ValueError, "usage"):
            inputs.pack(self.attempt, self.legacy, self.archive)

    def test_output_is_exclusive(self):
        inputs.pack(self.attempt, self.legacy, self.archive)
        with self.assertRaises(FileExistsError):
            inputs.pack(self.attempt, self.legacy, self.archive)

    def test_unexpected_tar_path_is_rejected_before_writing(self):
        with tarfile.open(self.archive, "w") as archive:
            info = tarfile.TarInfo("../escape")
            info.size = 2
            archive.addfile(info, io.BytesIO(b"{}"))
        output = self.root / "unpacked"
        with self.assertRaisesRegex(ValueError, "exactly"):
            inputs.unpack(self.archive, output)
        self.assertFalse(output.exists())

    def test_tar_links_are_rejected_before_writing(self):
        with tarfile.open(self.archive, "w") as archive:
            for name in inputs.FILES:
                info = tarfile.TarInfo(name)
                info.type = tarfile.SYMTYPE
                info.linkname = "/etc/passwd"
                archive.addfile(info)
        output = self.root / "unpacked"
        with self.assertRaisesRegex(ValueError, "links"):
            inputs.unpack(self.archive, output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
