"""Test verdict boundaries and fresh-output auditing, without emulating a VM."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from audit_host_results import LAB, audit
import reproduce_host


class HostReproductionTests(unittest.TestCase):
    def test_missing_engine_is_inconclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'attempt'
            with patch('sys.argv', ['reproduce_host.py', '--output', str(target)]), \
                    patch('reproduce_host.shutil.which', return_value=None), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(reproduce_host.main(), 2)
            report = json.loads((target / 'report.json').read_text())
            self.assertEqual(report['status'], 'INCONCLUSIVE')
            self.assertEqual(report['reason'], 'PODMAN_NOT_INSTALLED')
            self.assertNotIn('independentAudit', report)

    def test_existing_output_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('sys.argv', ['reproduce_host.py', '--output', directory]):
                with self.assertRaises(FileExistsError):
                    reproduce_host.main()

    def test_accounting_and_gate_reject_changed_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'outputs'
            # Work only on copies; the historical SQLite/WAL reference bytes stay untouched.
            shutil.copytree(LAB / 'reference-results', target)
            # The historical source hashes describe LF Git blobs, even on a CRLF Windows checkout.
            source = Path(directory) / 'historical-source'
            names = list(json.loads((target / 'bank/summary.json').read_text())['sourceSha256'])
            for name in names + ['contracts/cases.json', 'tools/verify_offline.py']:
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(subprocess.check_output(['git', 'show', 'HEAD:lab/' + name], cwd=LAB))
            def check():
                with patch('audit_host_results.LAB', source):
                    return audit(target)
            report = check()
            self.assertEqual(report['positiveDatabases'], 9)
            self.assertEqual(report['rejectedCorruptDatabases'], 1)
            path = target / 'none-observations.json'
            original = path.read_bytes()
            rows = json.loads(original)
            rows[0]['candidate'] = 'INVALID|99999999'
            path.write_text(json.dumps(rows))
            with self.assertRaises(AssertionError):
                check()
            path.write_bytes(original)
            path = target / 'no-mandate-gate.json'
            report = json.loads(path.read_text())
            report['release'] = 'SIMULATED_ALLOW'
            path.write_text(json.dumps(report))
            with self.assertRaises(AssertionError):
                check()


if __name__ == '__main__':
    unittest.main()
