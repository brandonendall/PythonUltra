"""PythonUltra UI4: wrapped file viewer, terminal handoff, and PyEditorRC-style turbo navigation."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
EDITOR = ROOT / "modules" / "pyeditor" / "__init__.py"
FILES = ROOT / "modules" / "pyfiles" / "__init__.py"
MARKER = "PYTHONULTRA_UI4_VERSION = 1"


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit("UI4 patch could not locate " + label)
    return text.replace(old, new, 1)


def replace_method(text, name, next_name, body):
    start_token = "    def " + name + "(self):\n"
    next_token = "    def " + next_name + "(self"
    start = text.find(start_token)
    if start < 0:
        raise SystemExit("UI4 patch could not locate method " + name)
    end = text.find(next_token, start + len(start_token))
    if end < 0:
        raise SystemExit("UI4 patch could not locate method after " + name)
    return text[:start] + body + "\n" + text[end:]


def patch_editor():
    text = EDITOR.read_text(encoding="utf-8")
    if MARKER in text:
        print("PythonUltra UI4 editor already applied")
        return

    # Port the proven PyEditorRC repeat model: an initial held-key delay, then
    # a short repeat threshold while scrolling. The is_scrolling flag is also
    # used by draw() to temporarily skip expensive syntax highlighting.
    start = text.index("class _KeyReader:")
    end = text.index("\ndef _maps(g):", start)
    reader = '''class _KeyReader:
    """Physical key reader with the proven PyEditorRC turbo repeat model."""
    def __init__(self, g):
        self.g = g
        self.pending = []
        self.repeat_keys = (g.KEY_UP, g.KEY_DOWN, g.KEY_LEFT, g.KEY_RIGHT, g.KEY_DEL)
        self.last_k = None
        self.rep_cnt = 0
        self.is_scrolling = False

    def read(self, fast_repeat=False):
        g = self.g
        while True:
            while True:
                ev = g.pollevent()
                if ev.type == g.KEYEV_NONE:
                    break
                if ev.type == g.KEYEV_DOWN:
                    self.pending.append(ev.key)
                    self.last_k = ev.key
                    self.rep_cnt = 0
                    self.is_scrolling = False
                elif ev.type == g.KEYEV_UP and ev.key == self.last_k:
                    was_scrolling = self.is_scrolling
                    self.last_k = None
                    self.rep_cnt = 0
                    self.is_scrolling = False
                    if was_scrolling and fast_repeat and not self.pending:
                        return None
            if self.pending:
                return self.pending.pop(0)

            if fast_repeat and self.last_k in self.repeat_keys:
                if g.keydown(self.last_k):
                    self.rep_cnt += 1
                    threshold = 6 if self.is_scrolling else 20
                    if self.rep_cnt > threshold:
                        self.rep_cnt = 5
                        self.is_scrolling = True
                        return self.last_k
                else:
                    was_scrolling = self.is_scrolling
                    self.last_k = None
                    self.rep_cnt = 0
                    self.is_scrolling = False
                    if was_scrolling:
                        return None
            time.sleep(0.01)
'''
    text = text[:start] + reader + text[end:]

    text = replace_once(text,
        "EDITOR_NAV_VERSION = 1\n",
        "EDITOR_NAV_VERSION = 1\n" + MARKER + "\n",
        "UI4 marker")

    text = replace_once(text,
        "        self.shift_active = False\n        self.clipboard = \"\"\n",
        "        self.shift_active = False\n        self.turbo_mode = True\n        self.clipboard = \"\"\n",
        "turbo state")

    vars_body = '''    def vars_menu(self):
        """Open SHIFT+VARS with editor style, RC turbo, and jump commands."""
        turbo_label = "Turbo: ON" if self.turbo_mode else "Turbo: OFF"
        action = self.popup("SHIFT VARS", (
            "Editor Style", turbo_label, "Jump to Top", "Jump to Bottom",
            "Jump to Line #", "Cancel"))
        if action == "Editor Style":
            self.style_menu()
        elif action == turbo_label:
            self.turbo_mode = not self.turbo_mode
            self._keys.is_scrolling = False
            self._keys.rep_cnt = 0
            self.msg = "Turbo ON" if self.turbo_mode else "Turbo OFF"
        elif action == "Jump to Top":
            self.jump_top()
        elif action == "Jump to Bottom":
            self.jump_bottom()
        elif action == "Jump to Line #":
            self.jump_line()
'''
    text = replace_method(text, "vars_menu", "catalog_menu", vars_body)

    turbo_draw = '''    def draw_line_turbo(self, text, y):
        """Fast plain-text renderer used only while a navigation key is held."""
        if self.scroll_x >= len(text):
            return
        visible = text[self.scroll_x:self.scroll_x + MAX_COLS + 2]
        if visible:
            self.g.dtext(TEXT_X, y, self.palette[FG], visible)

'''
    if "    def draw_line_turbo(self, text, y):\n" not in text:
        anchor = "    def _ensure_visible(self):\n"
        if anchor not in text:
            raise SystemExit("UI4 patch could not locate editor visibility method")
        text = text.replace(anchor, turbo_draw + anchor, 1)

    old_draw = '''            self.draw_line(self.lines[index], row * FONT_H, index)
'''
    new_draw = '''            if self.turbo_mode and self._keys.is_scrolling:
                self.draw_line_turbo(self.lines[index], row * FONT_H)
            else:
                self.draw_line(self.lines[index], row * FONT_H, index)
'''
    text = replace_once(text, old_draw, new_draw, "turbo draw path")

    text = replace_once(text,
        "                key = self._keys.read(fast_repeat=True)\n",
        "                key = self._keys.read(fast_repeat=self.turbo_mode)\n                if key is None:\n                    continue\n",
        "editor turbo read")

    EDITOR.write_text(text, encoding="utf-8")
    print("PythonUltra UI4 editor: PyEditorRC turbo navigation applied")


def patch_files():
    text = FILES.read_text(encoding="utf-8")
    if MARKER in text:
        print("PythonUltra UI4 files already applied")
        return

    text = replace_once(text,
        '__version__ = "0.7.0-cg50"\n',
        '__version__ = "0.7.1-cg50"\n' + MARKER + '\n',
        "Files UI4 marker")

    helper_anchor = '''def _modified_text(value):
'''
    helper = '''def _wrap_view_lines(text, width=46):
    """Wrap logical text lines for the calculator viewer without losing text."""
    wrapped = []
    for logical in str(text).replace("\\r\\n", "\\n").replace("\\r", "\\n").split("\\n"):
        if logical == "":
            wrapped.append("")
            continue
        remaining = logical
        while len(remaining) > width:
            cut = remaining.rfind(" ", 0, width + 1)
            if cut <= 0:
                cut = width
                wrapped.append(remaining[:cut])
                remaining = remaining[cut:]
            else:
                wrapped.append(remaining[:cut])
                remaining = remaining[cut + 1:]
        wrapped.append(remaining)
    return wrapped or [""]


'''
    if helper not in text:
        text = text.replace(helper_anchor, helper + helper_anchor, 1)

    text = replace_once(text,
        '        lines = text.split("\\n") if text else [""]\n',
        '        lines = _wrap_view_lines(text, 46)\n',
        "viewer wrapping")
    text = replace_once(text,
        '                g.dtext(4, HEADER_H + row * 11, p[1], lines[idx][:48])\n',
        '                g.dtext(4, HEADER_H + row * 11, p[1], lines[idx])\n',
        "viewer clipping")

    text = replace_once(text,
        '''            elif key == g.KEY_F2:\n                self.edit_file(path); return\n''',
        '''            elif key == g.KEY_F2:\n                return self.edit_file(path)\n''',
        "file-info edit return")
    text = replace_once(text,
        '''            elif key == g.KEY_F4:\n                if lower.endswith(".py"): self.run_file(path); return\n''',
        '''            elif key == g.KEY_F4:\n                if lower.endswith(".py"): return self.run_file(path)\n''',
        "file-info run return")
    text = replace_once(text,
        '''        self.file_info(path)\n\n    def run_file(self, path=None):\n''',
        '''        return self.file_info(path)\n\n    def run_file(self, path=None):\n''',
        "enter selected return")
    text = replace_once(text,
        '''            exec(code, scope, scope); self.msg = "Run OK"\n''',
        '''            exec(code, scope, scope); self.msg = "Run OK"\n            return "terminal"\n''',
        "run file terminal return")
    text = replace_once(text,
        '''            self.pyeditor.open_file(path, self.theme_name)\n            self.refresh()\n''',
        '''            result = self.pyeditor.open_file(path, self.theme_name)\n            self.refresh()\n            if result == "run":\n                return "terminal"\n''',
        "editor run terminal return")
    text = replace_once(text,
        '''        elif choice == "Run file": self.run_file()\n        elif choice == "Edit file": self.edit_file()\n''',
        '''        elif choice == "Run file":\n            if self.run_file() == "terminal": return "terminal"\n        elif choice == "Edit file":\n            if self.edit_file() == "terminal": return "terminal"\n''',
        "more menu terminal return")
    text = replace_once(text,
        '''            elif key in (g.KEY_EXE, g.KEY_RIGHT): self.enter_selected()\n''',
        '''            elif key in (g.KEY_EXE, g.KEY_RIGHT):\n                if self.enter_selected() == "terminal": return "terminal"\n''',
        "browser enter terminal return")
    text = replace_once(text,
        '''            elif key == g.KEY_F6:\n                if self.more_menu() == "exit": return\n            elif key == g.KEY_OPTN:\n                if self.more_menu() == "exit": return\n''',
        '''            elif key == g.KEY_F6:\n                action = self.more_menu()\n                if action in ("exit", "terminal"): return action\n            elif key == g.KEY_OPTN:\n                action = self.more_menu()\n                if action in ("exit", "terminal"): return action\n''',
        "browser menu terminal return")

    FILES.write_text(text, encoding="utf-8")
    print("PythonUltra UI4 files: wrapping and terminal handoff applied")


def main():
    patch_editor()
    patch_files()


if __name__ == "__main__":
    main()
