"""Regression checks for RC-controlled PythonUltra startup selection."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parents[3]
PYTERM_PATH = ROOT / "ports" / "sh" / "modules" / "pyterm" / "__init__.py"
MAIN_PATH = ROOT / "ports" / "sh" / "main.c"

fake_permissions = types.ModuleType("pyperm")
fake_permissions.is_dir = lambda path: False
sys.modules["pyperm"] = fake_permissions

spec = importlib.util.spec_from_file_location("pythonultra_pyterm_startup_test", PYTERM_PATH)
pyterm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pyterm)


def reload_from(path):
    pyterm.RC_PATH = str(path)
    pyterm._STARTED = False
    pyterm.startup()
    return pyterm.startup_view()


with tempfile.TemporaryDirectory() as temp_root:
    root = Path(temp_root)

    # Preserve the recovered run130.1 template. Missing/invalid startup in an existing
    # RC still falls back to Files; an explicit RC selection wins.
    missing = root / "default.rc"
    assert reload_from(missing) == 0
    assert "set startup=terminal" in missing.read_text(encoding="utf-8")

    terminal = root / "terminal.rc"
    terminal.write_text("set startup=terminal\n", encoding="utf-8")
    assert reload_from(terminal) == 0

    files = root / "files.rc"
    files.write_text("set startup=files\n", encoding="utf-8")
    assert reload_from(files) == 1

    invalid = root / "invalid.rc"
    invalid.write_text("set startup=automatic\n", encoding="utf-8")
    assert reload_from(invalid) == 1

    assert pyterm.menu_border() == 0xF800
    colors = root / "colors.rc"
    for spec, expected in (("red", 0xF800), ("'#00ff00'", 0x07E0),
                           ("0x001f", 0x001F), ("black", 0),
                           ("#ff0000", 0xF800), ("#ffffff", 0xFFFF),
                           ("invalid", 0xF800), ("0x10000", 0xF800),
                           ("#zzffff", 0xF800)):
        colors.write_text("set menu_border=" + spec + "\n", encoding="utf-8")
        reload_from(colors)
        assert pyterm.menu_border() == expected, spec
    # Removing the setting and reloading restores red, not a stale override.
    reload_from(terminal)
    assert pyterm.menu_border() == 0xF800
    assert pyterm.dispatch("modules") == 41

main = MAIN_PATH.read_text(encoding="utf-8")
assert "MP_QSTR_startup_view" in main
assert "if(pe_pyterm_call_int0(MP_QSTR_startup_view))" in main
assert "if(action == 41) pe_insert_catalog_selection();" in main

print("PythonUltra RC startup regression checks passed")
