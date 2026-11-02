"""Guided COBOL -> .NET 10 walkthrough. Same logic as the reference run; user-facing text in English."""
import argparse, json, os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
os.chdir(ROOT)
p = argparse.ArgumentParser(description='Step-by-step COBOL to .NET 10 demonstration')
p.add_argument('--auto', action='store_true', help='Run without pauses')
p.add_argument('--bank', action='store_true', help='Also run the transactional bank module')
a = p.parse_args()


def step(title, text):
    print('\n' + title + '\n' + text, flush=True)
    if not a.auto:
        input('Press Enter to continue... ')


def call(*args):
    subprocess.run([sys.executable, *args], check=True)


step('1 Open the COBOL program',
     'The program reads a 14-character record and uses REDEFINES to interpret its fields.')
print(pathlib.Path('legacy/fee.cob').read_text(), flush=True)

step('2 Run it locally',
     'The runner compiles with GnuCOBOL and executes the real binary. Half a cent rounds up to one cent.')
record = '0000002500200Y'
if not a.auto:
    entered = input('14-character record (Enter uses 0000002500200Y): ').strip()
    if entered:
        record = entered
if not re.fullmatch('[0-9]{13}[YN]', record):
    raise SystemExit('Invalid format: 8 amount digits + 5 rate digits + Y/N')
call('cobol_local.py', 'legacy/fee.cob', '--input', record)

step('3 Read the C# candidate',
     'The candidate implements the same policy and has modes that inject three deliberate defects.')
print(pathlib.Path('Candidate/Program.cs').read_text(), flush=True)

step('4 Run the comparison and the gate controls',
     'The .NET 10 candidate and gate are built. The 58 cases run against COBOL and C#, '
     'and every output is checked against the approved contract.')
call('run.py')

step('5 See why delivery is blocked',
     'An observed FAIL is the correct outcome when we inject a defect. INCONCLUSIVE also blocks. '
     'PASS without a mandate blocks delivery.')
s = json.loads(pathlib.Path('results/summary.json').read_text())
for name, r in s['reports'].items():
    print(f"{name:24} {r['verdict']:13} {r['release']}", flush=True)

step('6 From a calculation to transactions',
     'The bank module uses independent processes and a real SQLite database. It tests races, '
     'duplicates and recovery. It is not a mainframe benchmark.')
if a.bank or (not a.auto and input('Run the bank module? [y/N] ').lower() == 'y'):
    call('bank_test.py')

if a.bank:
    step('7 Greenfield business contract',
         'Run a NEW in-memory .NET 10 implementation from hypothetical business behavior, '
         'then independently verify its full output using a Python oracle. No COBOL translation.')
    call('greenfield/run_contract.py')

print('\nDone. Open results/summary.json, and results/bank/summary.json if you ran the bank module.',
      flush=True)
