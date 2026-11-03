"""Durable, provider-specific observations for disposable loopback experiments.

This records evidence, not a placement policy or an accounting decision.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import uuid


def utc():
    return datetime.now(timezone.utc).isoformat()


def capture(observe):
    """Observer unavailability is data, never an empty successful result."""
    try:
        return {'observationSucceeded': True, 'value': observe()}
    except Exception as exc:
        return {'observationSucceeded': False, 'exceptionType': type(exc).__name__,
                'error': str(exc)}


class PlacementJournal:
    def __init__(self, directory, provider, *, execution_id=None, metadata=None):
        if provider not in ('development', 'adonet'):
            raise ValueError('Unknown membership provider')
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.execution_id = execution_id or uuid.uuid4().hex
        if not self.execution_id.isalnum():
            raise ValueError('Execution ID must be alphanumeric')
        self.provider = provider
        self.stem = f'e2-loopback-{provider}-{self.execution_id}'
        self.journal_path = self.directory / (self.stem + '-observations.jsonl')
        self.failure_path = self.directory / (self.stem + '-failure.json')
        self.manifest_path = self.directory / (self.stem + '-manifest.json')
        self.sequence = 0
        # Exclusive creation must not replace an earlier original observation.
        self.stream = self.journal_path.open('x', encoding='utf-8')
        self.metadata = {**(metadata or {}), 'schemaVersion': 1, 'executionId': self.execution_id,
                         'membershipProvider': provider, 'startUtc': utc()}
        self._manifest('STARTED')
        self.append('execution-started')

    def _write(self, path, data):
        temporary = path.with_suffix(path.suffix + '.tmp')
        with temporary.open('w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)

    def _manifest(self, status, **data):
        self._write(self.manifest_path, {**self.metadata, 'status': status, **data})

    def append(self, kind, **data):
        self.sequence += 1
        event = {**self.metadata, 'sequence': self.sequence, 'eventUtc': utc(),
                 'kind': kind, **data}
        self.stream.write(json.dumps(event) + '\n')
        self.stream.flush()
        os.fsync(self.stream.fileno())
        return event

    def fail(self, exception, *, phase, state, logs=None):
        copied = {}
        for role, source in (logs or {}).items():
            if role not in ('primary', 'secondary'):
                raise ValueError('Unknown silo role')
            if source is not None and Path(source).is_file():
                raw = Path(source).read_bytes()
                destination = self.directory / (self.stem + '-' + role + '.log')
                with destination.open('xb') as stream:
                    stream.write(raw)
                copied[role] = {'file': destination.name, 'bytes': len(raw),
                                'sha256': hashlib.sha256(raw).hexdigest()}
        self.append('execution-failed', phase=phase, exceptionType=type(exception).__name__,
                    error=str(exception))
        record = {**self.metadata, 'status': 'FAIL', 'phase': phase, 'endUtc': utc(),
                  'exceptionType': type(exception).__name__, 'error': str(exception),
                  'state': state, 'logs': copied, 'journalFile': self.journal_path.name,
                  'journalSha256': hashlib.sha256(self.journal_path.read_bytes()).hexdigest(),
                  'classification': 'FAILED_OR_INCOMPLETE_NOT_ACCEPTED',
                  'isSuccessfulFailoverEvidence': False}
        self._write(self.failure_path, record)
        self._manifest('FAIL', failureFile=self.failure_path.name)
        return record

    def succeed(self, legacy_path):
        path = Path(legacy_path)
        expected = 'e2-adonet-recovery.json' if self.provider == 'adonet' else 'e2-multiprocess.json'
        if path.name != expected or path.parent.resolve() != self.directory.resolve():
            raise ValueError('Success must use the exact provider-specific result file')
        result = json.loads(path.read_text(encoding='utf-8'))
        if result.get('status') != 'PASS' or result.get('membershipProvider') != self.provider:
            raise ValueError('Success file does not identify this membership provider')
        self.append('execution-succeeded', successFile=path.name)
        self._manifest('PASS', successFile=path.name,
                       successSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                       journalFile=self.journal_path.name,
                       journalSha256=hashlib.sha256(self.journal_path.read_bytes()).hexdigest())

    def close(self):
        self.stream.close()
