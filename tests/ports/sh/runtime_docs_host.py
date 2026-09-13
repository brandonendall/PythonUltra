"""Build a real MicroPython host and test runtime docs, not CPython's help."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def run(*args):
    """Run a preparation or build command at the repository root, failing on error."""
    subprocess.run(args, cwd=ROOT, check=True)


parser = argparse.ArgumentParser()
parser.add_argument('--prepared', action='store_true')
args = parser.parse_args()
if not args.prepared:
    for script in ('apply_runtime_fixes', 'apply_pythonultra_features',
                   'apply_pythonultra_ui2', 'apply_pythonultra_permissions',
                   'apply_pythonultra_ui3_compat', 'apply_pythonultra_symbols',
                   'apply_pythonultra_symbol_safety', 'apply_pythonultra_editor_nav',
                   'apply_pythonultra_editor_nav_docs', 'apply_pythonultra_ui4',
                   'apply_pythonultra_info_menu', 'apply_pythonultra_cfiles',
                   'apply_pythonultra_execution_docs'):
        run(sys.executable, 'ports/sh/' + script + '.py')
    run(sys.executable, 'tools/pythonultra_docs.py', '--output',
        'build-module-docs/reference', '--runtime-header', 'ports/sh/module_docs.h')
reference = (ROOT / 'build-module-docs/reference/picoc.txt').read_text()
header = (ROOT / 'ports/sh/module_docs.h').read_text()
for signature in ('run(source, call_main=False)', 'run_file(path, call_main=True)', 'version()'):
    assert signature in reference, 'Missing PicoC reference: ' + signature
    assert signature in header, 'Missing PicoC runtime help: ' + signature
assert 'MP_QSTR_picoc' in header
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
