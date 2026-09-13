'''Patch PythonUltra editor navigation and held-key speed.'''

from pathlib import Path

EDITOR = Path(__file__).resolve().parent / "modules" / "pyeditor" / "__init__.py"
MARKER = "EDITOR_NAV_VERSION = 1"


def swap(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit("Unable to locate editor navigation block: " + label)
    return text.replace(old, new, 1)


def main():
    text = EDITOR.read_text(encoding="utf-8")
    if MARKER in text:
        print("PythonUltra editor navigation already applied")
        return

    text = swap(text,
        "EDITOR_FIXES_VERSION = 1\n",
        "EDITOR_FIXES_VERSION = 1\nEDITOR_NAV_VERSION = 1\n",
        "version marker")

    old_reader = '''class _KeyReader:
    """Drain releases before acting on repeats; preserve real presses in order."""
    def __init__(self, g):
        self.g = g
        self.pending = []
        self.repeat_keys = (g.KEY_UP, g.KEY_DOWN, g.KEY_LEFT, g.KEY_RIGHT, g.KEY_DEL)

    def read(self):
        g = self.g
        while True:
            repeat = None
            while True:
                ev = g.pollevent()
                if ev.type == g.KEYEV_NONE:
                    break
                if ev.type == g.KEYEV_DOWN:
                    self.pending.append(ev.key)
                    repeat = None
                elif ev.type == g.KEYEV_HOLD and ev.key in self.repeat_keys:
                    repeat = ev.key
                elif ev.type == g.KEYEV_UP and ev.key == repeat:
                    repeat = None
            if self.pending:
                return self.pending.pop(0)
            # keydown() reflects processed events, so it is only current after
            # draining the queue. Coalesce a backlog to at most one movement.
            if repeat is not None and g.keydown(repeat):
                return repeat
            time.sleep(0.01)
'''
    new_reader = '''class _KeyReader:
    """Drain events and optionally synthesize fast repeat for the editor."""
    FAST_REPEAT_DELAY = 0.18
    FAST_REPEAT_INTERVAL = 0.03

    def __init__(self, g):
        self.g = g
        self.pending = []
        self.repeat_keys = (g.KEY_UP, g.KEY_DOWN, g.KEY_LEFT, g.KEY_RIGHT, g.KEY_DEL)
        self.held_key = None
        self.repeat_at = 0.0

    def read(self, fast_repeat=False):
        g = self.g
        while True:
            hold_event = None
            now = time.time()
            while True:
                ev = g.pollevent()
                if ev.type == g.KEYEV_NONE:
                    break
                if ev.type == g.KEYEV_DOWN:
                    self.pending.append(ev.key)
                    if ev.key in self.repeat_keys:
                        self.held_key = ev.key
                        self.repeat_at = now + self.FAST_REPEAT_DELAY
                elif ev.type == g.KEYEV_HOLD and ev.key in self.repeat_keys:
                    self.held_key = ev.key
                    hold_event = ev.key
                    if self.repeat_at <= 0.0:
                        self.repeat_at = now + self.FAST_REPEAT_DELAY
                elif ev.type == g.KEYEV_UP and ev.key == self.held_key:
                    self.held_key = None
                    self.repeat_at = 0.0
            if self.pending:
                return self.pending.pop(0)

            held = self.held_key
            if held is not None and not g.keydown(held):
                self.held_key = None
                self.repeat_at = 0.0
                held = None

            if fast_repeat and held is not None:
                now = time.time()
                if now >= self.repeat_at:
                    self.repeat_at = now + self.FAST_REPEAT_INTERVAL
                    return held
            elif hold_event is not None and g.keydown(hold_event):
                return hold_event

            time.sleep(0.005 if fast_repeat else 0.01)
'''
    text = swap(text, old_reader, new_reader, "key reader")

    old_style = '''    def style_menu(self):
        action = self.popup("Editor Style", ("Syntax Theme", "Font / Size", "Cancel"))
        if action == "Syntax Theme":
            choice = self.popup("Syntax Theme", THEME_NAMES)
            if choice:
                self.set_theme(choice)
        elif action == "Font / Size":
            choice = self.popup("Editor Font", FONT_OPTIONS)
            if choice:
                self.apply_font(choice)

    def catalog_menu(self):
'''
    new_style = '''    def style_menu(self):
        action = self.popup("Editor Style", ("Syntax Theme", "Font / Size", "Cancel"))
        if action == "Syntax Theme":
            choice = self.popup("Syntax Theme", THEME_NAMES)
            if choice:
                self.set_theme(choice)
        elif action == "Font / Size":
            choice = self.popup("Editor Font", FONT_OPTIONS)
            if choice:
                self.apply_font(choice)

    def jump_top(self):
        self.cy = 0
        self.cx = 0
        self.goal_x = 0
        self.scroll_x = 0
        self.scroll_y = 0
        self.msg = "Top"
        self._ensure_visible()

    def jump_bottom(self):
        self.cy = max(0, len(self.lines) - 1)
        self.cx = len(self.lines[self.cy])
        self.goal_x = self.cx
        self.scroll_x = 0
        self.scroll_y = max(0, self.cy - MAX_ROWS + 1)
        self.msg = "Bottom"
        self._ensure_visible()

    def jump_line(self):
        value = self.input_bar("Jump to line", str(self.cy + 1))
        if value is None:
            return
        try:
            line_number = int(value)
        except (TypeError, ValueError):
            self.msg = "Line number?"
            return
        line_number = max(1, min(len(self.lines), line_number))
        self.cy = line_number - 1
        self.cx = 0
        self.goal_x = 0
        self.scroll_x = 0
        self.msg = "Line " + str(line_number)
        self._ensure_visible()

    def vars_menu(self):
        action = self.popup("SHIFT VARS", (
            "Editor Style", "Jump to Top", "Jump to Bottom",
            "Jump to Line #", "Cancel"))
        if action == "Editor Style":
            self.style_menu()
        elif action == "Jump to Top":
            self.jump_top()
        elif action == "Jump to Bottom":
            self.jump_bottom()
        elif action == "Jump to Line #":
            self.jump_line()

    def catalog_menu(self):
'''
    text = swap(text, old_style, new_style, "SHIFT VARS commands")

    text = swap(text,
'''                if self.shift_active and key == g.KEY_VARS:
                    self.shift_active = False
                    self.style_menu()
                    continue
''',
'''                if self.shift_active and key == g.KEY_VARS:
                    self.shift_active = False
                    self.vars_menu()
                    continue
''', "input-bar SHIFT VARS")

    text = swap(text,
'''                    if key == g.KEY_VARS:
                        self.shift_active = False
                        self.style_menu()
                        continue
''',
'''                    if key == g.KEY_VARS:
                        self.shift_active = False
                        self.vars_menu()
                        continue
''', "editor SHIFT VARS")

    text = swap(text,
'''                key = self._keys.read()
                if key in (g.KEY_F1, g.KEY_F2, g.KEY_F3, g.KEY_F4, g.KEY_F5):
''',
'''                key = self._keys.read(fast_repeat=True)
                if key in (g.KEY_F1, g.KEY_F2, g.KEY_F3, g.KEY_F4, g.KEY_F5):
''', "editor fast repeat")

    EDITOR.write_text(text, encoding="utf-8")
    print("Applied PythonUltra editor navigation and fast repeat")


if __name__ == "__main__":
    main()
