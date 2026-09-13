"""Date editor validation, cancellation, saving and readback behavior."""
from datetime import datetime, timedelta
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ports/sh/modules"))
import pythonultra
from pythonultra import clock

assert clock.validate((2000, 2, 29, 23, 59, 59)) == (2000, 2, 29, 23, 59, 59)
for fields in ((2026, 2, 29, 0, 0, 0), (1900, 2, 29, 0, 0, 0),
               (2026, 4, 31, 0, 0, 0), (2026, 1, 1, 24, 0, 0),
               (2026, 1, 1, 0, 60, 0), (2026, 1, 1, 0, 0, 60)):
    try:
        clock.validate(fields)
        raise AssertionError(fields)
    except ValueError:
        pass


class FakeTime(types.ModuleType):
    def __init__(self):
        super().__init__("time")
        self.now = (2026, 9, 11, 10, 11, 12)
        self.writes = []
    def localtime(self):
        return self.now + (4, 254)
    def set_datetime(self, fields):
        self.writes.append(tuple(fields))
        self.now = tuple(fields)
    def mktime(self, fields):
        return int((datetime(*fields[:6]) - datetime(1970, 1, 1)).total_seconds())
    def sleep_ms(self, ms):
        pass


class FakeGint:
    def __init__(self):
        for i, key in enumerate(("EXIT", "UP", "DOWN", "EXE", "ADD", "SUB", "F1")
                                 + tuple(str(n) for n in range(10))):
            setattr(self, "KEY_" + key, i + 1)
        self.KEYEV_DOWN, self.KEYEV_HOLD = 1, 2
        self.keys, self.text, self.frames = [], [], []
    def dfont_builtin(self, name): self.font = name
    def dfont(self, value): self.font = None
    def clearevents(self): pass
    def drect(self, *args): pass
    def drect_border(self, *args): self.frames.append(args)
    def dtext(self, x, y, color, text):
        assert 0 <= x and x + self.dsize(text)[0] <= 395
        assert 0 <= y <= 214
        self.text.append(text)
    def dsize(self, text): return len(text) * 7, 10
    def dupdate(self): pass
    def pollevent(self):
        return types.SimpleNamespace(type=self.KEYEV_DOWN, key=self.keys.pop(0))


time = FakeTime()
g = FakeGint()
sys.modules["time"] = time
sys.modules["gint"] = g
pythonultra.menu_border = lambda: 0xF800
g.keys = [g.KEY_2, g.KEY_0, g.KEY_2, g.KEY_8, g.KEY_EXIT]
assert clock.show(True) is False
assert not time.writes and g.font is None
assert g.frames[0][4:] == (0, 2, 0xF800)

g.keys = [g.KEY_2, g.KEY_0, g.KEY_2, g.KEY_8, g.KEY_F1]
assert clock.show(True) is True
assert time.writes[-1] == (2028, 9, 11, 10, 11, 12)
assert "2028-09-11 10:11:12" == clock.clock_text()

count = len(time.writes)
g.keys = [g.KEY_DOWN, g.KEY_1, g.KEY_3, g.KEY_F1, g.KEY_EXIT]
assert clock.show(False) is False
assert len(time.writes) == count
assert "Month must be 1 to 12" in g.text

# Saving at midnight can legitimately advance the date during readback.
def rollover(fields):
    d = datetime(*fields) + timedelta(seconds=1)
    time.now = (d.year, d.month, d.day, d.hour, d.minute, d.second)
time.set_datetime = rollover
clock.save((2028, 2, 29, 23, 59, 59))
assert time.now == (2028, 3, 1, 0, 0, 0)
time.set_datetime = lambda fields: None
try:
    clock.save((2026, 1, 1, 0, 0, 0))
    raise AssertionError("failed readback accepted")
except OSError:
    pass
time.now = (2026, 13, 1, 0, 0, 0)
assert clock.clock_text().startswith("Unavailable")
print("PythonUltra clock UI: save/cancel, bounds, invalid dates and readback passed")
