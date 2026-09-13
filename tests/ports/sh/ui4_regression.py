"""Regression checks for PythonUltra UI4 calculator usability fixes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EDITOR = ROOT / "ports" / "sh" / "modules" / "pyeditor" / "__init__.py"
FILES = ROOT / "ports" / "sh" / "modules" / "pyfiles" / "__init__.py"

editor = EDITOR.read_text(encoding="utf-8")
files = FILES.read_text(encoding="utf-8")

editor_required = (
    "PYTHONULTRA_UI4_VERSION = 1",
    "self.last_k = None",
    "self.rep_cnt = 0",
    "self.is_scrolling = False",
    "threshold = 6 if self.is_scrolling else 20",
    "self.rep_cnt = 5",
    "self.is_scrolling = True",
    "self.turbo_mode = True",
    '"Turbo: ON" if self.turbo_mode else "Turbo: OFF"',
    "def draw_line_turbo(self, text, y):",
    "self.turbo_mode and self._keys.is_scrolling",
    "self._keys.read(fast_repeat=self.turbo_mode)",
)
files_required = (
    "PYTHONULTRA_UI4_VERSION = 1",
    "def _wrap_view_lines(text, width=46):",
    "lines = _wrap_view_lines(text, 46)",
    'return "terminal"',
    'if result == "run":',
    'if self.enter_selected() == "terminal": return "terminal"',
)

missing = [item for item in editor_required if item not in editor]
if missing:
    raise SystemExit("UI4 editor regression missing: " + repr(missing))
missing = [item for item in files_required if item not in files]
if missing:
    raise SystemExit("UI4 files regression missing: " + repr(missing))

if "lines[idx][:48]" in files:
    raise SystemExit("UI4 viewer regression: hard clipping remains")

print("UI4 regression: ok")
