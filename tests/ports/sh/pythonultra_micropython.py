"""Portable smoke scenario: MicroPython script MODULE_DIR EMPTY_TEMP_DIR."""
import os
import sys

sys.path.insert(0, sys.argv[1])
root = sys.argv[2]
import zipfile
import pyterm
import pyperm
pyperm._cache = {}

source = root + "/original.txt"
with open(source, "w") as out:
    out.write("PythonUltra round trip\n" * 100)
archive = root + "/original.zip"
zipfile.compress(source, archive)
assert zipfile.namelist(archive) == ("original.txt",)
zipfile.extract(archive, root + "/extracted")
with open(source) as a:
    with open(root + "/extracted/original.txt") as b:
        assert a.read() == b.read()

pyterm.RC_PATH = root + "/rc"
with open(pyterm.RC_PATH, "w") as out:
    out.write("set startup=terminal\nset menu_border=#ff0000\n")
pyterm._STARTED = False
pyterm.startup()
assert pyterm.startup_view() == 0
assert pyterm.menu_border() == 0xF800
import pythonultra
assert pythonultra.catalog_text("numpy", "array") == "numpy.array"
assert pythonultra.catalog_text("builtins", "print") == "print"

class FakeGint:
    def __init__(self):
        self.next_key = 1
        self.font = "small"
    def __getattr__(self, name):
        if name.startswith("KEY_"):
            value = self.next_key
            self.next_key += 1
            setattr(self, name, value)
            return value
        raise AttributeError(name)
    def dfont_builtin(self, name):
        self.font = name
        return (9, 10)
    def dsize(self, text):
        return (len(text) * 6 - (1 if text else 0), 10)
sys.modules["gint"] = FakeGint()
import pyeditor
editor = pyeditor.Editor(source)
editor.lines = ["headTAIL"]
editor.cx = 4
editor.insert("one\ntwo\nthree")
assert editor.lines == ["headone", "two", "threeTAIL"]
assert editor.save_file()
with open(source) as check:
    assert check.read() == "headone\ntwo\nthreeTAIL"
assert not editor.load_file(root + "/absent.txt")
assert editor.lines == ["headone", "two", "threeTAIL"]
g = sys.modules['gint']
g.KEYEV_NONE, g.KEYEV_DOWN, g.KEYEV_UP, g.KEYEV_HOLD = 0, 1, 2, 3
class Event:
    def __init__(self, kind, key):
        self.type, self.key = kind, key
events = [Event(g.KEYEV_DOWN, g.KEY_RIGHT)] + [
    Event(g.KEYEV_HOLD, g.KEY_RIGHT) for _ in range(30)
] + [Event(g.KEYEV_UP, g.KEY_RIGHT), Event(g.KEYEV_DOWN, g.KEY_LOG)]
def poll():
    return events.pop(0) if events else Event(g.KEYEV_NONE, 0)
g.pollevent = poll
g.keydown = lambda key: False
assert editor._keys.read() == g.KEY_RIGHT
assert editor._keys.read() == g.KEY_LOG
editor.alpha_mode, editor.shift_active = 1, True
assert editor.resolve_char(g.KEY_LOG) == 'B'
assert editor.resolve_char(g.KEY_MUL) == 'S'
assert editor._input_mode() == 'A'
print("Real MicroPython ZIP/editor/RC/Catalog smoke passed")
