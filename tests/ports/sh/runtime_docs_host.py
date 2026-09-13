"""Build a real MicroPython host and test runtime docs, not CPython's help."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


parser = argparse.ArgumentParser()
parser.add_argument('--prepared', action='store_true')
args = parser.parse_args()
if not args.prepared:
    for script in ('apply_runtime_fixes', 'apply_pythonultra_features',
                   'apply_pythonultra_ui2', 'apply_pythonultra_permissions',
                   'apply_pythonultra_ui3_compat', 'apply_pythonultra_symbols'):
        run(sys.executable, 'ports/sh/' + script + '.py')
    run(sys.executable, 'tools/pythonultra_docs.py', '--output',
        'build-module-docs/reference', '--runtime-header', 'ports/sh/module_docs.h')
build = ROOT / 'build-docs-host'
run('make', '-C', 'ports/unix', '-j2', 'VARIANT=doc_variant',
    'VARIANT_DIR=' + str(ROOT / 'tests/ports/sh/doc_variant'), 'BUILD=' + str(build))
result = subprocess.run([str(build / 'micropython'),
    'tests/ports/sh/runtime_docs_micropython.py', str(ROOT)],
    cwd=ROOT, capture_output=True, text=True)
output = result.stdout
if result.returncode:
    print(output)
    print(result.stderr, file=sys.stderr)
    raise SystemExit(result.returncode)
assert 'vec3(x=0.0, y=0.0, z=0.0)' in output, output
assert 'sqrt' in output and 'square root' in output, output
assert 'Members (help(module.member)' in output, output
assert '<function' not in output and '<bound_method' not in output, output
assert output.rstrip().endswith('runtime documentation: PASS'), output
print(output)
