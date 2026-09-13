"""Exercise prepared Files routing, permissions, and terminal error handoff."""
from pathlib import Path
import contextlib
import io
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ports/sh/modules"))
calls = []
sys.modules["picoc"] = types.SimpleNamespace(run_file=lambda path: calls.append(path) or 0)
import pyfiles

browser = pyfiles.FileManager.__new__(pyfiles.FileManager) if hasattr(pyfiles, "FileManager") else None
# Resolve the browser class without invoking calculator drawing initialization.
if browser is None:
    cls = next(value for value in vars(pyfiles).values()
               if isinstance(value, type) and hasattr(value, "enter_selected"))
    browser = cls.__new__(cls)
with tempfile.TemporaryDirectory() as folder:
    browser.folder = folder
    source = Path(folder) / "smoke.C"
    source.write_text("int main(void) { return 0; }\n")
    browser.selected_entry = lambda: (source.name, False)
    browser.file_info = lambda path: "info"
    checked = []
    pyfiles.pyperm.require_read = lambda path: checked.append(path)
    old_path = list(sys.path)
    with contextlib.redirect_stdout(io.StringIO()) as output:
        assert browser.enter_selected() == "terminal"
    assert calls == [str(source)] and checked == [str(source)]
    assert "C exit code: 0" in output.getvalue()
    assert sys.path == old_path
    browser.selected_entry = lambda: ("notes.txt", False)
    assert browser.enter_selected() == "info"
    def denied(path):
        raise PermissionError("read denied")
    pyfiles.pyperm.require_read = denied
    with contextlib.redirect_stdout(io.StringIO()) as output:
        assert browser.run_file(str(source)) == "terminal"
    assert "read denied" in output.getvalue() and len(calls) == 1
    pyfiles.pyperm.require_read = lambda path: None
    sys.modules["picoc"].run_file = lambda path: 3
    with contextlib.redirect_stdout(io.StringIO()) as output:
        assert browser.run_file(str(source)) == "terminal"
    assert "C exit code: 3" in output.getvalue()
    assert browser.msg == "C error"
print("C-file selection, permissions, and terminal handoff: PASS")
