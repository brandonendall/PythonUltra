"""Catalog names, cancellation, bounded popup layout and native insertion."""
import importlib.util
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "pythonultra", ROOT / "ports/sh/modules/pythonultra/__init__.py")
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)
ui.menu_border = lambda: 0xF800

assert ui.catalog_text("builtins", "print") == "print"
assert ui.catalog_text("numpy", "array") == "numpy.array"
assert ui.catalog_text("math", "pi") == "math.pi"

real_popup = ui.popup
choices = iter(("numpy", "array"))
ui.popup = lambda *args: next(choices)
assert ui.catalog_insert_ui() == "numpy.array"
choices = iter(("builtins", "print"))
assert ui.catalog_insert_ui() == "print"
choices = iter((None,))
assert ui.catalog_insert_ui() is None
# Cancel a member list, then cancel the module list: no accidental insertion.
choices = iter(("numpy", None, None))
assert ui.catalog_insert_ui() is None
ui.popup = real_popup


class FakeGint(types.ModuleType):
    def __init__(self):
        super().__init__("gint")
        names = ("EXIT", "LEFT", "EXE", "RIGHT", "UP", "DOWN", "ADD", "SUB",
                 "1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
        for index, name in enumerate(names):
            setattr(self, "KEY_" + name, index + 1)
        self.KEYEV_DOWN, self.KEYEV_HOLD = 1, 2
        self.keys = []
        self.text = []
        self.frames = []
        self.font = "large"
        self.drains = 0
    def dfont_builtin(self, name):
        self.font = name
    def dfont(self, font):
        self.font = "default"
    def dsize(self, text):
        return len(text) * 7, 10
    def dtext(self, x, y, color, text):
        assert self.font == "small"
        self.text.append((x, y, color, text))
    def drect(self, *args):
        pass
    def drect_border(self, *args):
        self.frames.append(args)
    def dupdate(self):
        pass
    def clearevents(self):
        self.drains += 1
    def pollevent(self):
        return types.SimpleNamespace(type=self.KEYEV_DOWN, key=self.keys.pop(0))


g = FakeGint()
sys.modules["gint"] = g
g.keys = [g.KEY_DOWN, g.KEY_EXE]
assert ui.popup("Long menu title " * 5, ("first", "second" * 50), True) == "second" * 50
assert g.font == "default"
assert g.drains == 1
assert g.frames[0][4] == 0xF800
for x, y, color, text in g.text:
    assert x >= 0 and x + g.dsize(text)[0] <= 362
    assert 0 <= y and y + 10 <= 224
g.keys = [g.KEY_EXIT]
assert ui.popup("Cancel", ("first",)) is None
g.keys = [g.KEY_2]
assert ui.popup("Number select", ("first", "second")) == "second"

# Dark information pages use their own readable, scrollable framed treatment;
# Catalog/editor popups above retain their existing behavior.
g.frames.clear()
g.text.clear()
g.keys = [g.KEY_DOWN, g.KEY_EXE]
assert ui.information_panel("PythonUltra Info", tuple("line" + str(i) for i in range(16)), True) is None
assert g.frames[0][4] == 0xF800
assert any(text == "line10" for _, _, _, text in g.text)

# This test runs after the build patches. The F3 path must insert into the
# existing edit line, without clearing it or evaluating the selected name.
main = (ROOT / "ports/sh/main.c").read_text(encoding="utf-8")
assert "MP_QSTR_catalog_insert_ui" in main
start = main.index("static void pe_insert_catalog_selection(void)")
end = main.index("static int pe_terminal_dispatch", start)
helper = main[start:end]
assert "console_write_raw(PE.console, text, length);" in helper
assert "console_clear_current_line(" not in helper
assert "pyexec_repl_execute(code)" not in helper
assert "dfont(previous_font);" in helper
assert "pe_run_python_action(\"import pythonultra as _pu; _pu.catalog_ui" not in main
print("PythonUltra Catalog insertion/color/layout checks passed")
