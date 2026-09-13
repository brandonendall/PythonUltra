"""Host-side regression checks for PythonUltra editor navigation preparation."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EDITOR = ROOT / "ports" / "sh" / "modules" / "pyeditor" / "__init__.py"
text = EDITOR.read_text(encoding="utf-8")

# Navigation must preserve the proven PyEditorRC held-key model rather than the
# abandoned staged/timer repeat experiment. Turbo starts after 20 polls, then
# repeats at the original short threshold while lightweight drawing is active.
required = (
    "EDITOR_NAV_VERSION = 1",
    "PYTHONULTRA_UI4_VERSION = 1",
    'self.popup("SHIFT VARS"',
    '"Editor Style", turbo_label, "Jump to Top", "Jump to Bottom"',
    '"Jump to Line #", "Cancel"',
    "def jump_top(self):",
    "def jump_bottom(self):",
    "def jump_line(self):",
    "def vars_menu(self):",
    "def read(self, fast_repeat=False):",
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

missing = [item for item in required if item not in text]
if missing:
    raise SystemExit("pyeditor navigation regression: missing " + repr(missing))

# Popup/input helpers should keep the default conservative repeat path.
if text.count("self._keys.read()") < 2:
    raise SystemExit("pyeditor navigation regression: popup/input repeat changed")

# Guard against accidentally restoring the discarded staged/timer turbo model.
for stale in ("TURBO_DELAY_MS = 120", "TURBO_INTERVAL_MS = 18", "def repeat_step(self):"):
    if stale in text:
        raise SystemExit("pyeditor navigation regression: stale turbo model restored: " + stale)

print("pyeditor navigation regression: PyEditorRC turbo ok")
