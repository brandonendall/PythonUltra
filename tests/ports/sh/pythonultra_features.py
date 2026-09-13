"""Build-time regression checks for PythonUltra calculator features."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
SH = ROOT / "ports" / "sh"
FXCG = ROOT / "ports" / "fxcg50"
MODULES = SH / "modules"

sys.path.insert(0, str(MODULES))
import numpy as np

# The public frozen package must own the numpy name. The native helper stays
# private so numpy.matrix is visible on actual calculator hardware.
native = (SH / "modnumpy.c").read_text(encoding="utf-8")
assert "MP_REGISTER_MODULE(MP_QSTR__numpy_fast, modnumpy_module);" in native
assert "MP_REGISTER_MODULE(MP_QSTR_numpy, modnumpy_module);" not in native

m = np.matrix([[4.0, 7.0], [2.0, 6.0]])
assert m.T.tolist() == [[4.0, 2.0], [7.0, 6.0]]
ident = m * m.I
assert abs(ident[0, 0] - 1.0) < 1e-5
assert abs(ident[0, 1]) < 1e-5
assert np.cross([1, 0, 0], [0, 1, 0]) == [0, 0, 1]
assert abs(np.norm([3, 4]) - 5.0) < 1e-9
assert np.normalize([0, 5]) == [0.0, 1.0]
assert np.lerp([0, 10], [10, 20], 0.5) == [5.0, 15.0]

main = (SH / "main.c").read_text(encoding="utf-8")
widget = (SH / "widget_shell.c").read_text(encoding="utf-8")
widget_h = (SH / "widget_shell.h").read_text(encoding="utf-8")
config = (SH / "mpconfigport.h").read_text(encoding="utf-8")
manifest = (SH / "manifest.py").read_text(encoding="utf-8")
modgint = (SH / "modgint.c").read_text(encoding="utf-8")
modos = (SH / "modos.c").read_text(encoding="utf-8")
fdfile = (SH / "fdfile.c").read_text(encoding="utf-8")
pathutil = (SH / "pathutil.c").read_text(encoding="utf-8")
pyterm = (MODULES / "pyterm" / "__init__.py").read_text(encoding="utf-8")
pyfiles = (MODULES / "pyfiles" / "__init__.py").read_text(encoding="utf-8")
pyeditor = (MODULES / "pyeditor" / "__init__.py").read_text(encoding="utf-8")
pyperm = (MODULES / "pyperm" / "__init__.py").read_text(encoding="utf-8")
pyultra = (MODULES / "pythonultra" / "__init__.py").read_text(encoding="utf-8")
pyzip = (MODULES / "zipfile" / "__init__.py").read_text(encoding="utf-8")
metadata = (FXCG / "fxconv-metadata.txt").read_text(encoding="utf-8")
makefile = (FXCG / "Makefile").read_text(encoding="utf-8")

# Native shell UI and PythonUltra help/catalog/info integration.
assert "pythonultra_help_text" in main
assert "MICROPY_PY_BUILTINS_HELP_TEXT     pythonultra_help_text" in config
assert "key == KEY_F3" in main and "MP_QSTR_catalog_insert_ui" in main
assert "key == KEY_F4" in main and "pe_apply_theme()" in main
assert "key == KEY_F5" in main and "pyeditor" in main
assert "key == KEY_F6" in main and "_pu.info_ui(" in main
assert "pe_terminal_dispatch" in main and "MP_QSTR_pyterm" in main
assert "pe_terminal_load_startup" in main and "pe_terminal_apply_config" in main
assert "pe_apply_terminal_font" in main
assert "if(pe_pyterm_call_int0(MP_QSTR_startup_view))" in main

# Persistent history and SHIFT+DEL programming-symbol insertion.
assert "widget_shell_history_recall" in widget
assert "widget_shell_history_push" in widget
assert "widget_shell_history_add" in widget and "widget_shell_history_clear" in widget
assert "WIDGET_SHELL_SYMBOLS" in widget and "WIDGET_SHELL_SYMBOLS" in widget_h
assert "KEY_DEL" in widget and "ev.shift" in widget
assert "MP_QSTR_symbol_ui" in main and "console_write_raw" in main
assert "def symbol_ui(" in pyultra and "_PROGRAMMING_SYMBOLS" in pyultra
# Symbols are intentionally created from ASCII codes at runtime. Literal frozen
# punctuation can surface as QSTR-safe names such as _hyphen_ on the fx-CG50.
assert "_PROGRAMMING_SYMBOL_CODES" in pyultra
assert "tuple(chr(code) for code in _PROGRAMMING_SYMBOL_CODES)" in pyultra
for code in (64, 35, 36, 37, 94, 38, 42, 33, 60, 62, 61, 43, 45,
             47, 92, 124, 95, 40, 41, 91, 93, 123, 125, 39, 34, 58,
             59, 44, 46):
    assert str(code) in pyultra

# Embedded system + JetBrains terminal fonts and measured editor font control.
assert "modgint_dfont_builtin" in modgint and "OBJ(dfont_builtin)" in modgint
assert "modgint_dsize" in modgint and "OBJ(dsize)" in modgint
assert "font_jb_9" in modgint and "font_jb_13" in modgint and "font_jb_19" in modgint
assert "font_jb_9.png" in metadata and "font_jb_13.png" in metadata and "font_jb_19.png" in metadata
assert "prepare_jetbrains_mono.py" in makefile and "apply_pythonultra_ui3_compat.py" in makefile
assert "EDITOR_FIXES_VERSION = 1" in pyeditor
assert "apply_font" in pyeditor and '"System Small", "System Normal", "System Large"' in pyeditor
assert "self.g.dsize(text)" in pyeditor
assert '"JetBrains Small", "JetBrains Normal"' not in pyeditor

# Virtual current working directory: terminal/os/open/imports share one path layer.
assert "pe_path_getcwd" in pathutil and "pe_path_chdir" in pathutil and "pe_path_resolve" in pathutil
assert "pe_path_getcwd" in modos and "pe_path_chdir" in modos and "pe_path_resolve" in modos
assert "pe_path_resolve" in fdfile
assert "request == MP_STREAM_SEEK" in fdfile and "GINT_CALL(fdfile_world_seek" in fdfile
assert "seek->offset = call.result" in fdfile and "request == MP_STREAM_FLUSH" in fdfile
assert "struct stat st = {0};" in modos
assert "#define MICROPY_PY_ERRNO" in config
assert "pe_path_getcwd" in main and "pe_path_resolve" in main
# Reject actual bare libc cwd calls while allowing PythonUltra wrappers such as
# pe_os_getcwd(), pe_os_chdir(), pe_path_getcwd() and pe_path_chdir().
assert re.search(r"(?<![A-Za-z0-9_])getcwd\s*\(", modos) is None
assert re.search(r"(?<![A-Za-z0-9_])chdir\s*\(", modos) is None

# Frozen public modules.
assert 'freeze("modules", "pythonultra", opt=3)' in manifest
assert 'freeze("modules", "pyeditor", opt=3)' in manifest
assert 'freeze("modules", "pyfiles", opt=3)' in manifest
assert 'freeze("modules", "pyperm", opt=3)' in manifest
assert 'freeze("modules", "pyterm", opt=3)' in manifest
assert 'freeze("modules", "zipfile", opt=3)' in manifest

# Linux-like terminal behavior, help flags, rc/history, permissions and files.
assert "def dispatch(" in pyterm
assert '"-h"' in pyterm and '"--help"' in pyterm
assert '"--h"' in pyterm and '"-help"' in pyterm
assert "zip" in pyterm and "unzip" in pyterm
assert '"chmod"' in pyterm and "pyperm.chmod" in pyterm
assert 'RC_PATH = "/.pythonultrarc"' in pyterm
assert 'HISTORY_PATH = "/.pythonultra_history"' in pyterm
assert '"alias"' in pyterm and '"history"' in pyterm and '"font"' in pyterm
assert 'cmd.startswith("./")' in pyterm and "require_execute" in pyterm
assert "FONT_JB_SMALL" in pyterm and "FONT_JB_NORMAL" in pyterm and "FONT_JB_LARGE" in pyterm
assert "def history_tail(" in pyterm and "def config(" in pyterm
assert '"startup": "files"' in pyterm and "def startup_view(" in pyterm
assert 'value in ("files", "terminal")' in pyterm

assert "create_new" in pyfiles and "rename_selected" in pyfiles and "delete_selected" in pyfiles
assert "permission_menu" in pyfiles and "pyperm.require_write" in pyfiles
assert "compress_selected" in pyfiles and "extract_selected" in pyfiles
assert 'result == "run"' not in pyfiles
assert "GitHub Dark" in pyeditor and "GitHub Light" in pyeditor and "Linux" in pyeditor
assert "pyperm.require_write" in pyeditor
assert "_cleanup(created_files, created_folders)" in pyzip
assert 'DB_PATH = "/.pythonultra_permissions"' in pyperm
assert "def format_mode" in pyperm and "def executable" in pyperm

print("PythonUltra feature regression checks passed")
