"""Local COBOL runner. GnuCOBOL compiles to a native executable; this is not an interpreter or an emulator."""
import argparse, os, pathlib, subprocess, sys, tempfile

p = argparse.ArgumentParser(description='Compile and run a console COBOL program locally with GnuCOBOL')
p.add_argument('source', type=pathlib.Path)
p.add_argument('--input', default='0000002500200Y', help='Line sent to the program through stdin')
p.add_argument('--fixed', action='store_true', help='Use fixed source format instead of free format')
a = p.parse_args()
source = a.source.resolve()
if not source.is_file():
    p.error('COBOL source file not found')

with tempfile.TemporaryDirectory(prefix='cobol-local-') as directory:
    exe = pathlib.Path(directory) / 'program'
    command = [os.environ.get('COBC', 'cobc'), '-x', *([] if a.fixed else ['-free']), '-o', str(exe), str(source)]
    print('Compile:', ' '.join(command), flush=True)
    result = subprocess.run(command, timeout=120)
    if result.returncode:
        sys.exit(result.returncode)
    print('Input:', repr(a.input), flush=True)
    result = subprocess.run([str(exe)], input=a.input + '\n', text=True, timeout=30)
    sys.exit(result.returncode)
