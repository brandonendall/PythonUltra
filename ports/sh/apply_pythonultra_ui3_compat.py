'''Compatibility launcher for the PythonUltra UI3 patch stage.

The canonical editor owns its font restoration and physical-event input path;
the legacy editor substitutions must not overwrite its tested implementation.

UI3 also adds string-based font selectors to modgint.c. Ensure the generated C
source declares strcmp() explicitly so the SH cross-compiler can build it with
implicit-function declarations treated as errors.

Hardware follow-up: UI2/UI3 initialize the native Terminal first so RC settings,
font, theme and persistent history can be restored. After initialization, honor
the RC startup preference: Files by default or Terminal when explicitly set.
The compatibility stage also avoids frozen-QSTR punctuation
names and defaults the editor to the known-good system font until JetBrains Mono
raster generation is fixed on hardware.

Editor hardware follow-up: the original PyEditorRC prototype reads physical key
events with pollevent()/keydown(), but the frozen editor refactor switched to a
blocking getkey_opt() call that temporarily rewrites the shared keydev_std()
transform. F5 launches the editor synchronously from inside JustUI's key-event
handler, so that transform handoff is unsafe on calculator hardware. Restore a
polling input path and discard the launcher's stale event tail before the editor
takes ownership of keyboard input.
'''

from pathlib import Path

import apply_pythonultra_ui3 as ui3

_original_replace_once = ui3.replace_once


def _compatible_replace_once(text, old, new, label):
    if label == "restore default font on editor exit":
        if new in text:
            return text, False
        if old not in text:
            return text, False
    return _original_replace_once(text, old, new, label)


def _ensure_string_header():
    path = Path(__file__).with_name("modgint.c")
    text = path.read_text(encoding="utf-8")
    if "#include <string.h>" in text:
        return
    marker = "#include <stdlib.h>\n"
    if marker not in text:
        raise SystemExit("Unable to locate modgint standard include block")
    text = text.replace(marker, marker + "#include <string.h>\n", 1)
    path.write_text(text, encoding="utf-8")


def _prefer_files_startup():
    path = Path(__file__).with_name("main.c")
    text = path.read_text(encoding="utf-8")
    marker = '''    //=== Event handling ===//
'''
    injected = '''    /* The RC can select Terminal explicitly. Missing/invalid startup
       settings retain the PythonUltra hardware default of enhanced Files. */
    if(pe_pyterm_call_int0(MP_QSTR_startup_view)) {
        if(pe_dark_mode)
            pe_run_python_action("import pyfiles as _pf; _pf.browse('/', 'GitHub Dark')");
        else
            pe_run_python_action("import pyfiles as _pf; _pf.browse('/', 'GitHub Light')");
    }
    pe_show_shell();

    //=== Event handling ===//
'''
    if injected in text:
        return
    if marker not in text:
        raise SystemExit("Unable to locate PythonUltra event-loop marker")
    path.write_text(text.replace(marker, injected, 1), encoding="utf-8")


def _runtime_help_separator():
    path = Path(__file__).with_name("modules") / "pyterm" / "__init__.py"
    text = path.read_text(encoding="utf-8")
    old = '    print("-" * 30)\n'
    new = '    print(chr(45) * 30)\n'
    if new in text:
        return
    if old not in text:
        raise SystemExit("Unable to locate PythonUltra manual separator")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _catalog_command():
    path = Path(__file__).with_name("main.c")
    text = path.read_text(encoding="utf-8")
    old = '''                else if(action == 40) pe_terminal_apply_config();
                pe_print_terminal_prompt();
'''
    new = old + '''                if(action == 41) pe_insert_catalog_selection();
'''
    if new in text:
        return
    if old not in text:
        raise SystemExit("Unable to locate native Catalog command insertion")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _safe_editor_default_font():
    path = Path(__file__).with_name("modules") / "pyeditor" / "__init__.py"
    text = path.read_text(encoding="utf-8")
    if "EDITOR_FIXES_VERSION = 1" in text:
        return
    old = 'DEFAULT_FONT = "JetBrains Small"\n'
    new = 'DEFAULT_FONT = "System Small"\n'
    if new in text:
        return
    if old not in text:
        raise SystemExit("Unable to locate PythonUltra editor default font")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _safe_editor_input():
    path = Path(__file__).with_name("modules") / "pyeditor" / "__init__.py"
    text = path.read_text(encoding="utf-8")
    if "EDITOR_FIXES_VERSION = 1" in text:
        return

    old_imports = '''import gc
import sys
'''
    new_imports = '''import gc
import sys
import time
'''
    if new_imports not in text:
        if old_imports not in text:
            raise SystemExit("Unable to locate PythonUltra editor import block")
        text = text.replace(old_imports, new_imports, 1)

    old_reader = '''def _raw_key(g):
    """Read a key without gint consuming SHIFT/ALPHA as modifiers."""
    try:
        opts = g.GETKEY_DEFAULT & ~(g.GETKEY_MOD_SHIFT | g.GETKEY_MOD_ALPHA)
        return g.getkey_opt(opts, None).key
    except Exception:
        # Older compatible builds can still fall back to getkey().
        return g.getkey().key
'''
    new_reader = '''def _raw_key(g):
    """Read physical key events without rewriting the shared key transform."""
    while True:
        ev = g.pollevent()
        if ev.type == g.KEYEV_DOWN:
            return ev.key
        if ev.type == g.KEYEV_HOLD and ev.key in (
            g.KEY_UP, g.KEY_DOWN, g.KEY_LEFT, g.KEY_RIGHT, g.KEY_DEL
        ):
            return ev.key
        time.sleep(0.01)
'''
    if new_reader not in text:
        if old_reader not in text:
            raise SystemExit("Unable to locate PythonUltra editor raw-key block")
        text = text.replace(old_reader, new_reader, 1)

    old_run = '''    def run(self):
        g = self.g
        while True:
'''
    new_run = '''    def run(self):
        g = self.g
        # F5/EXE comes from JustUI. Drain its release/modifier tail before the
        # editor starts reading the same global keyboard event queue directly.
        g.clearevents()
        while True:
'''
    if new_run not in text:
        if old_run not in text:
            raise SystemExit("Unable to locate PythonUltra editor run loop")
        text = text.replace(old_run, new_run, 1)

    path.write_text(text, encoding="utf-8")


ui3.replace_once = _compatible_replace_once

if __name__ == "__main__":
    ui3.main()
    _ensure_string_header()
    _prefer_files_startup()
    _runtime_help_separator()
    _catalog_command()
    _safe_editor_default_font()
    _safe_editor_input()
