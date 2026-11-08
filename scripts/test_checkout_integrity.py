"""Verify that checkout settings cannot rewrite hashed sources or raw evidence."""
from pathlib import Path
import subprocess
import tempfile
import unittest

import build


ROOT = Path(__file__).resolve().parents[1]


class CheckoutIntegrityTests(unittest.TestCase):
    def test_generated_books_use_canonical_utf8_lf(self):
        for language in build.EDITIONS:
            with self.subTest(language=language):
                path, text = build.render(language)
                self.assertEqual(path.read_bytes(), text.encode("utf-8"))

    def test_checkout_preserves_source_and_evidence_bytes(self):
        attributes = (ROOT / ".gitattributes").read_bytes()
        fixtures = {
            "lab/contracts/cases.json": b'[{"id": "test"}]\n',
            "lab/legacy/fee.cob": b"identification division.\n",
            "lab/Candidate/Program.cs": b"Console.WriteLine(1);\n",
            "lab/bank_test.py": b"print(1)\n",
            "lab/scripts/run-podman.sh": b"#!/bin/bash\nexit 0\n",
            "book/figures/src/en/agent_chain.mmd": b"flowchart LR\nA --> B\n",
            "book/figures/theme.json": b'{"theme": "base"}\n',
            "book/figures/theme.css": b"svg { color: red; }\n",
            "book/en.md": b"# Book\n",
            "evidence/reproduction/host.log": b"original\r\noutput\r\n",
            "evidence/runs/result.json": b'{"status": "PASS"}\r\n',
            "lab/reference-results/summary.json": b'{"original": true}\r\n',
            "lab/reference-results/bank/acceptance.db": b"SQLite format 3\0\r\n",
            "book/figures/en/agent_chain.png": b"\x89PNG\r\n\x1a\n\0",
            "evidence/maintenance/history.bundle": b"# bundle\n\0\r\n",
            "evidence/editorial/original.zip": b"PK\0\r\n",
        }
        with tempfile.TemporaryDirectory(prefix="book-checkout-") as directory:
            root = Path(directory)

            def git(*args):
                return subprocess.run(
                    ["git", *args], cwd=root, check=True, capture_output=True,
                )

            git("init", "--quiet")
            git("config", "core.autocrlf", "false")
            (root / ".gitattributes").write_bytes(attributes)
            for name, content in fixtures.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            git("add", "--all")
            for setting in ("true", "input", "false"):
                with self.subTest(autocrlf=setting):
                    for name in fixtures:
                        (root / name).unlink()
                    git("-c", f"core.autocrlf={setting}", "checkout-index", "--all", "--force")
                    for name, expected in fixtures.items():
                        self.assertEqual((root / name).read_bytes(), expected, name)


if __name__ == "__main__":
    unittest.main()
