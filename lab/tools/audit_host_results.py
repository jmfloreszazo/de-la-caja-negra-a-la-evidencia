"""Read fresh lab outputs with the existing read-only accounting oracle."""
import ast
import hashlib
import json
import pathlib
import sqlite3

LAB = pathlib.Path(__file__).resolve().parents[1]


def audit(results):
    results = pathlib.Path(results)
    summary = json.loads((results / 'summary.json').read_text())
    bank = json.loads((results / 'bank/summary.json').read_text())
    assert summary['status'] == bank['status'] == 'PASS'
    assert summary['cases'] == 58 and summary['gateControls'] == 10
    cases = json.loads((LAB / 'contracts/cases.json').read_text())
    rows = json.loads((results / 'none-observations.json').read_text())
    assert len(rows) == len(cases) == 58
    assert {r['id'] for r in rows} == {c['id'] for c in cases}
    expected = {c['id']: c['expected'] for c in cases}
    assert all(r['legacy'] == r['candidate'] == expected[r['id']] for r in rows)
    gate = {'none': ('PASS', 0), 'round-even': ('FAIL', 2), 'wrong-threshold': ('FAIL', 2),
            'approve-inactive': ('FAIL', 2), 'missing-evidence': ('INCONCLUSIVE', 3),
            'missing-case': ('INCONCLUSIVE', 3), 'duplicate-case': ('INCONCLUSIVE', 3),
            'invalid-anchor': ('INCONCLUSIVE', 3), 'no-mandate': ('PASS', 4),
            'equal-but-wrong': ('FAIL', 2)}
    assert set(summary['reports']) == set(gate)
    for name, decision in gate.items():
        raw = json.loads((results / (name + '-gate.json')).read_text())
        assert (raw['verdict'], raw['exitCode']) == decision
        assert raw['release'] == ('SIMULATED_ALLOW' if name == 'none' else 'BLOCK')
        assert all(raw[k] == summary['reports'][name][k] for k in ['verdict', 'exitCode', 'release'])
    controls = bank['controls']
    assert set(controls) == {'overdraftRace', 'duplicateAndConflict', 'exceptionRollback',
                             'processCrashRecovery', 'commitWithoutResponse', 'lockWaitAndRetry',
                             'boundedRetries', 'accountingInvariants', 'oracleRejectsCorruptLedger'}
    assert all(v == 'PASS' for k, v in controls.items() if k != 'accountingInvariants')
    assert len(controls['accountingInvariants']) == 6 and all(controls['accountingInvariants'].values())
    for name, digest in bank['sourceSha256'].items():
        assert hashlib.sha256((LAB / name).read_bytes()).hexdigest() == digest, name
    oracle_path = LAB / 'tools/verify_offline.py'
    source = ast.parse(oracle_path.read_text())
    function = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'ledger_invariants')
    scope = {'pathlib': pathlib, 'sqlite3': sqlite3}
    # Execute the existing function alone; importing the module would inspect historical results.
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(oracle_path), 'exec'), scope)
    names = {'acceptance.db', 'negative-control.db'} | {
        f'load-{pattern}-{workers}.db' for pattern in ['uniform', 'hot'] for workers in [1, 2, 4, 8]}
    databases = list((results / 'bank').glob('*.db'))
    assert {p.name for p in databases} == names
    observations = {}
    for path in databases:
        predicates = scope['ledger_invariants'](path)
        assert len(predicates) == 6
        assert all(predicates.values()) if path.name != 'negative-control.db' else not all(predicates.values())
        observations[path.name] = predicates
    return {'status': 'PASS', 'feeCases': 58, 'gateControls': 10,
            'positiveDatabases': 9, 'rejectedCorruptDatabases': 1,
            'accountingPredicatesPerDatabase': 6, 'ledgerObservations': observations,
            'oracleSha256': hashlib.sha256(oracle_path.read_bytes()).hexdigest()}
