"""Regression checks for frozen-QSTR-safe punctuation insertion."""
import importlib.util
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[3]

# PythonUltra catalog must construct the separator at runtime.
spec = importlib.util.spec_from_file_location(
    "pythonultra_symbols_test", ROOT / "ports/sh/modules/pythonultra/__init__.py")
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)
assert ui.catalog_text("py3d", "cube") == "py3d.cube"
assert ui.catalog_text("numpy", "array") == "numpy.array"
expected_picker = tuple(chr(code) for code in (
    64,35,36,37,94,38,42,33,63,126,96,60,62,61,43,45,47,92,124,95,
    40,41,91,93,123,125,39,34,58,59,44,46))
assert ui._PROGRAMMING_SYMBOLS == expected_picker

# Load the editor and exercise all punctuation-producing physical key maps.
import sys
sys.path.insert(0, str(ROOT / "ports/sh/modules"))
spec = importlib.util.spec_from_file_location(
    "pyeditor_symbols_test", ROOT / "ports/sh/modules/pyeditor/__init__.py")
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)

names = "0 1 2 3 4 5 6 7 8 9 DOT ADD SUB MUL DIV LEFTPAR RIGHTPAR COMMA NEG EQUALS XOT LOG LN SIN COS TAN FRAC FD ARROW EXP VARS".split()
g = types.SimpleNamespace(**{"KEY_" + name: index for index, name in enumerate(names)})
base, alpha, shift = editor._maps(g)
assert base[g.KEY_DOT] == "."
assert base[g.KEY_ADD] == "+"
assert base[g.KEY_SUB] == "-"
assert base[g.KEY_MUL] == "*"
assert base[g.KEY_DIV] == "/"
assert base[g.KEY_LEFTPAR] == "("
assert base[g.KEY_RIGHTPAR] == ")"
assert base[g.KEY_COMMA] == ","
assert base[g.KEY_EQUALS] == "="
assert alpha[g.KEY_EXP] == '"'
assert alpha[g.KEY_VARS] == "_"
assert shift[g.KEY_MUL] == "{"
assert shift[g.KEY_DIV] == "}"
assert shift[g.KEY_ADD] == "["
assert shift[g.KEY_SUB] == "]"
assert shift[g.KEY_DOT] == "="
assert shift[g.KEY_0] == ":"
assert shift[g.KEY_EXP] == "3.14159"
assert editor.SYMBOLS == tuple(chr(code) for code in editor._SYMBOL_CODES)

# Source-level guard: punctuation-producing maps must use runtime chr(), not
# frozen one-character punctuation string values.
source = (ROOT / "ports/sh/modules/pyeditor/__init__.py").read_text(encoding="utf-8")
block = source[source.index("def _maps(g):"):source.index("class Editor:")]
for literal in ('KEY_DOT:"."', 'KEY_ADD:"+"', 'KEY_SUB:"-"', 'KEY_MUL:"*"',
                'KEY_DIV:"/"', 'KEY_LEFTPAR:"("', 'KEY_RIGHTPAR:")"',
                'KEY_COMMA:","', 'KEY_EQUALS:"="', 'KEY_EXP:\'"\'',
                'KEY_VARS:"_"'):
    assert literal not in block, literal

print("All PythonUltra editor/catalog punctuation paths are QSTR-safe")
