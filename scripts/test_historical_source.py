"""Offline negative controls for exact historical source byte verification."""
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from historical_source import verify_historical_source


class HistoricalSourceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.commit = "a" * 40
        self.path = "lab/example.py"
        self.raw = b"historical source\r\n"
        self.digest = hashlib.sha256(self.raw).hexdigest()

    def verify(self, digest=None):
        verify_historical_source(self.root, self.commit, self.path, digest or self.digest)

    def test_reads_original_snapshot_without_text_normalization(self):
        with patch.object(Path, "read_bytes", autospec=True, return_value=self.raw) as read:
            self.verify()
        read.assert_called_once_with(
            self.root / "evidence" / "historical-source" / self.commit / self.path)

    def test_changed_bytes_and_normalized_line_endings_fail(self):
        for raw in (b"changed\r\n", self.raw.replace(b"\r\n", b"\n")):
            with self.subTest(raw=raw), patch.object(Path, "read_bytes", return_value=raw):
                with self.assertRaisesRegex(ValueError, "Historical source mismatch"):
                    self.verify()

    def test_wrong_expected_hash_fails(self):
        with patch.object(Path, "read_bytes", return_value=self.raw):
            with self.assertRaisesRegex(ValueError, "Historical source mismatch"):
                self.verify("0" * 64)

    def test_missing_snapshot_fails_without_worktree_fallback(self):
        with patch.object(Path, "read_bytes", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                self.verify()

    def test_unpinned_revisions_and_invalid_digests_are_rejected(self):
        with patch.object(Path, "read_bytes") as read:
            for commit, digest in (("HEAD", self.digest), (self.commit, "invalid")):
                with self.subTest(commit=commit, digest=digest), self.assertRaises(ValueError):
                    verify_historical_source(self.root, commit, self.path, digest)
            read.assert_not_called()

    def test_paths_cannot_escape_historical_source_directory(self):
        with patch.object(Path, "read_bytes") as read:
            for path in ("../example.py", "/example.py", "C:/example.py", "..\\example.py"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    verify_historical_source(self.root, self.commit, path, self.digest)
            read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
