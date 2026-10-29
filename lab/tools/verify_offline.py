"""Offline verification that needs only Python 3 (no COBOL compiler, no .NET SDK).

It does NOT replace run.py or bank_test.py. It checks four things that can be checked without them:

1. The baseline anchor: contracts/cases.json still matches contracts/cases.sha256.
2. A third, independent implementation of the written policy (this file) reproduces every
   expected value in the baseline. If it disagrees, the contract or this reading of it is wrong.
3. Provenance: which source files are byte-identical to the ones hashed in the reference run.
4. The ledger oracle: the reference SQLite databases satisfy the accounting invariants,
   and the deliberately corrupted negative control is rejected.

Exit code 0 when every check behaves as expected.
"""
import hashlib, json, pathlib, re, sqlite3, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REF = ROOT / 'reference-results'
failures = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fee_policy(record: str) -> str:
    """Independent reading of the contract in the book (Annex B). Integer cents, basis points."""
    if not re.fullmatch(r'[0-9]{8}[0-9]{5}[YN]', record):
        return 'INVALID|00000000'
    amount, rate, active = int(record[:8]), int(record[8:13]), record[13]
    if rate > 10000:
        return 'INVALID|00000000'
    if active == 'N':
        return 'REJECT|00000000'
    quotient, remainder = divmod(amount * rate, 10000)
    fee = quotient + (1 if 2 * remainder >= 10000 else 0)  # nearest, ties away from zero (non-negative)
    if fee > 99_999_999:
        return 'INVALID|00000000'  # ON SIZE ERROR in the COBOL program
    return f"{'REVIEW' if amount > 1_000_000 else 'APPROVE'}|{fee:08d}"


def ledger_invariants(db: pathlib.Path) -> dict:
    """Same invariants as bank_test.py, evaluated read-only on persisted data."""
    with sqlite3.connect(f'file:{db}?mode=ro', uri=True) as c:
        def s(q):
            return c.execute(q).fetchone()[0]
        return {
            'nonnegative': s('SELECT MIN(balance) FROM accounts') >= 0,
            'conserved': s('SELECT SUM(balance) FROM accounts') == s('SELECT COUNT(*)*100000 FROM accounts'),
            'balancedPostings': s('SELECT COUNT(*) FROM (SELECT op FROM postings GROUP BY op '
                                  'HAVING SUM(delta)<>0 OR COUNT(*)<>2)') == 0,
            'twoPostingsPerCommit': s("SELECT COUNT(*) FROM operations o WHERE status='COMMITTED' AND "
                                      "(SELECT COUNT(*) FROM postings p WHERE p.op=o.id)<>2") == 0,
            'outboxAtomic': s("SELECT COUNT(*) FROM operations o WHERE status='COMMITTED' AND NOT EXISTS"
                              "(SELECT 1 FROM outbox b WHERE b.op=o.id)") == 0 and
                            s("SELECT COUNT(*) FROM outbox b JOIN operations o ON b.op=o.id "
                              "WHERE o.status<>'COMMITTED'") == 0,
            'projectionAgrees': s('SELECT COUNT(*) FROM accounts a WHERE balance<>100000+COALESCE('
                                  '(SELECT SUM(delta) FROM postings p WHERE p.account=a.id),0)') == 0,
        }


# 1. Baseline anchor
cases_path = ROOT / 'contracts' / 'cases.json'
anchor = (ROOT / 'contracts' / 'cases.sha256').read_text().strip()
anchor_ok = sha(cases_path) == anchor
print(f"[1] baseline anchor ............ {'OK' if anchor_ok else 'MISMATCH'}")
if not anchor_ok:
    failures.append('baseline anchor mismatch')

# 2. Independent policy implementation against every approved case
cases = json.loads(cases_path.read_text())
ids = [c['id'] for c in cases]
if len(ids) != len(set(ids)):
    failures.append('duplicate case ids in baseline')
disagreements = [(c['id'], c['input'], c['expected'], fee_policy(c['input']))
                 for c in cases if fee_policy(c['input']) != c['expected']]
print(f"[2] independent policy ......... {len(cases) - len(disagreements)}/{len(cases)} cases agree")
for d in disagreements:
    print('    DISAGREE', d)
    failures.append(f'policy disagreement {d[0]}')

# 3. Provenance of the reference run
summary = json.loads((REF / 'summary.json').read_text())
bank_summary = json.loads((REF / 'bank' / 'summary.json').read_text())
hashed = dict(summary['sourceSha256'])
hashed.update(bank_summary['sourceSha256'])
print('[3] provenance against the reference run (29 Oct 2026, native Linux):')
for rel, expected in sorted(hashed.items()):
    path = ROOT / rel
    if not path.is_file():
        state = 'MISSING'
    elif sha(path) == expected:
        state = 'identical'
    else:
        state = 'changed since reference run'
    print(f'    {rel:32} {state}')
    if state == 'MISSING':
        failures.append(f'missing {rel}')
core = ['legacy/fee.cob', 'Candidate/Program.cs', 'Gate/Program.cs', 'Bank/Program.cs',
        'contracts/cases.json', 'run.py', 'bank_test.py']
for rel in core:
    if sha(ROOT / rel) != hashed[rel]:
        failures.append(f'core file changed: {rel}')
print('    note: walkthrough.py and cobol_local.py were translated to English after the run '
      '(user-facing strings only); the core files above must stay identical.')

# 4. Ledger oracle on the persisted reference databases
print('[4] ledger oracle on reference databases:')
for db in sorted((REF / 'bank').glob('*.db')):
    result = ledger_invariants(db)
    passed = all(result.values())
    expected_pass = db.name != 'negative-control.db'
    verdict = 'PASS' if passed else 'REJECTED ' + ','.join(k for k, v in result.items() if not v)
    ok = passed == expected_pass
    print(f"    {db.name:24} {verdict:40} {'as expected' if ok else 'UNEXPECTED'}")
    if not ok:
        failures.append(f'ledger oracle unexpected on {db.name}')

print()
if failures:
    print('VERIFY: FAIL')
    for f in failures:
        print('  -', f)
    sys.exit(2)
print('VERIFY: PASS (offline checks only; run.py and bank_test.py still require GnuCOBOL and .NET 10)')
