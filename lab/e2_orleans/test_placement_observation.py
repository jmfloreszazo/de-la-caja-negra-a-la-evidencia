"""Negative controls for provenance and failed observation persistence."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from placement_observation import PlacementJournal, capture


class PlacementObservationTest(unittest.TestCase):
    def test_failure_does_not_reuse_a_previous_provider_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = root / 'e2-multiprocess.json'
            raw = b'{"membershipProvider":"development","status":"PASS"}\n'
            previous.write_bytes(raw)
            journal = PlacementJournal(root, 'adonet', execution_id='negative')
            journal.append('placement-probe', phase='placement-convergence',
                           accountHostPids={'1': 20}, sqlMembership={'status': 'unavailable'})
            logs = root / 'source.log'
            logs.write_bytes(b'E2_PLACEMENT_STRATEGY:ObservedPolicy\n\x00original\n')
            failure = journal.fail(AssertionError('Dual placement not observed'),
                                   phase='placement-convergence', state={'financialCommandsAttempted': 0},
                                   logs={'primary': logs})
            journal.close()
            self.assertEqual(previous.read_bytes(), raw)
            self.assertFalse((root / 'e2-adonet-recovery.json').exists())
            self.assertEqual(failure['status'], 'FAIL')
            self.assertFalse(failure['isSuccessfulFailoverEvidence'])
            self.assertEqual(failure['membershipProvider'], 'adonet')
            self.assertEqual((root / failure['logs']['primary']['file']).read_bytes(), logs.read_bytes())
            self.assertEqual(failure['journalSha256'], hashlib.sha256(journal.journal_path.read_bytes()).hexdigest())
            manifest = json.loads(journal.manifest_path.read_text())
            self.assertEqual(manifest['status'], 'FAIL')
            self.assertNotIn('successFile', manifest)

    def test_each_execution_and_attempt_remains_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            first = PlacementJournal(directory, 'development')
            second = PlacementJournal(directory, 'development')
            for attempt in range(1, 4):
                first.append('placement-probe', attempt=attempt, phase='placement-convergence')
            first.close()
            second.close()
            rows = [json.loads(s) for s in first.journal_path.read_text().splitlines()]
            self.assertEqual([r['sequence'] for r in rows], [1, 2, 3, 4])
            self.assertEqual([r['attempt'] for r in rows[1:]], [1, 2, 3])
            self.assertNotEqual(first.execution_id, second.execution_id)
            with self.assertRaises(FileExistsError):
                PlacementJournal(directory, 'development', execution_id=first.execution_id)

    def test_unavailable_observer_is_not_an_empty_success(self):
        def unavailable():
            raise RuntimeError('SQL not observable')
        result = capture(unavailable)
        self.assertFalse(result['observationSucceeded'])
        self.assertNotIn('value', result)
        self.assertIn('SQL not observable', result['error'])
        self.assertEqual(capture(lambda: []), {'observationSucceeded': True, 'value': []})

    def test_success_manifest_binds_exact_provider_file(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = PlacementJournal(directory, 'adonet')
            path = Path(directory) / 'e2-adonet-recovery.json'
            path.write_text('{"status":"PASS","membershipProvider":"adonet"}\n')
            journal.succeed(path)
            journal.close()
            manifest = json.loads(journal.manifest_path.read_text())
            self.assertEqual(manifest['successFile'], path.name)
            self.assertEqual(manifest['successSha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_wrong_provider_success_cannot_be_promoted(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = PlacementJournal(directory, 'adonet', metadata={'membershipProvider': 'development'})
            self.assertEqual(journal.metadata['membershipProvider'], 'adonet')
            wrong = Path(directory) / 'e2-multiprocess.json'
            wrong.write_text('{"status":"PASS","membershipProvider":"development"}')
            with self.assertRaises(ValueError):
                journal.succeed(wrong)
            impostor = Path(directory) / 'e2-adonet-recovery.json'
            impostor.write_bytes(wrong.read_bytes())
            with self.assertRaises(ValueError):
                journal.succeed(impostor)
            journal.close()
            self.assertEqual(json.loads(journal.manifest_path.read_text())['status'], 'STARTED')


if __name__ == '__main__':
    unittest.main()
