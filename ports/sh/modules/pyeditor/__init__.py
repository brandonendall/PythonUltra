"""Calculator-native PythonUltra text editor for the fx-CG50.

The editor uses gint's physical event queue, measures proportional glyphs with
``dsize()``, and keeps file operations bounded for the calculator heap.
"""

import gc
import os
import sys
import time
import pyperm
import errno

__version__ = "0.3.1-cg50"

# Build patch stages use this marker to leave this canonical implementation
# intact instead of replaying older editor string-replacement patches.
EDITOR_FIXES_VERSION = 1

SCREEN_W = 396
SCREEN_H = 224
NAV_H = 12
INFO_H = 12
BODY_H = SCREEN_H - NAV_H - INFO_H
TEXT_X = 2
MAX_EDIT_BYTES = 65536
MAX_EDIT_LINES = 2048

# The system fonts are known-good on both tested fx-CG50 display/OS revisions.
# JetBrains choices stay out of the editor until their raster data is verified
# on hardware. The first number is only a fallback width; dsize() is canonical.
FONT_OPTIONS = ("System Small", "System Normal", "System Large")
FONT_CONFIG = {
    "System Small": ("small", 9, 10),
    "System Normal": ("normal", 12, 17),
    "System Large": ("large", 18, 23),
}
DEFAULT_FONT = "System Small"
UI_FONT = "small"
UI_FONT_H = 10
FONT_W = 9
FONT_H = 10
MAX_ROWS = max(1, BODY_H // FONT_H)
MAX_COLS = max(4, (SCREEN_W - TEXT_X) // FONT_W)

THEMES = {
    "GitHub Dark": (0x0000, 0xD69A, 0x0000, 0xD69A, 0x2148, 0xFFFF, 0xFF7B, 0x7D7C, 0x79FF, 0xA59D, 0x8C71, 0xD39F, 0xFFA6, 0x3186),
    "GitHub Light": (0xFFFF, 0x18E3, 0xF7BE, 0x18E3, 0xBDF7, 0x0000, 0xA00F, 0x06B9, 0x045F, 0x0863, 0x6B6D, 0x7A6D, 0x9A63, 0xD69A),
    "Linux Terminal": (0x0000, 0xC618, 0x0000, 0x07E0, 0x03E0, 0x0000, 0xFFE0, 0x07FF, 0xF81F, 0x07E0, 0x8410, 0xFBE0, 0x07FF, 0x4208),
    "PythonUltra Dark": (0x0000, 0xFFFF, 0x0000, 0xC618, 0x07FF, 0x0000, 0xE004, 0x041F, 0xFB44, 0x8430, 0xF8F9, 0x7B5F, 0xBF3A, 0x528A),
    "PythonUltra Light": (0xFFFF, 0x0000, 0x0000, 0xFFFF, 0x07E0, 0xFFFF, 0x001F, 0x7800, 0xF800, 0x3549, 0x8410, 0xA81F, 0x7B5F, 0xD69A),
}
THEME_NAMES = tuple(THEMES)
DEFAULT_THEME = "GitHub Dark"

# Palette tuple indexes.
BG, FG, BAR, BAR_FG, SEL_BG, SEL_FG, KEYWORD, BUILTIN, NUMBER, STRING, COMMENT, DECORATOR, TYPE, BORDER = range(14)

KEYWORDS_FLOW = {"if", "else", "elif", "for", "while", "break", "continue", "return", "yield", "pass", "raise", "try", "except", "finally", "with", "async", "await", "match", "case", "from", "import"}
KEYWORDS_DEF = {"def", "class", "lambda", "global", "nonlocal"}
KEYWORDS_LOGIC = {"and", "or", "not", "in", "is", "del"}
KEYWORDS_CONST = {"True", "False", "None"}
KEYWORDS = KEYWORDS_FLOW | KEYWORDS_DEF | KEYWORDS_LOGIC | KEYWORDS_CONST
BUILTINS = {"abs", "all", "any", "bin", "bool", "bytearray", "bytes", "callable", "chr", "compile", "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter", "float", "format", "getattr", "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance", "iter", "len", "list", "locals", "map", "max", "memoryview", "min", "next", "object", "oct", "open", "ord", "pow", "print", "range", "repr", "reversed", "round", "set", "setattr", "slice", "sorted", "str", "sum", "tuple", "type", "vars", "zip"}
TYPES = {"int", "float", "str", "bool", "bytes", "bytearray", "list", "dict", "tuple", "set"}
MODULES = {"builtins", "gint", "numpy", "pygame", "py3d", "pythonultra", "pyeditor", "pyfiles", "ctypes", "os", "json", "time", "math", "random", "sys", "io", "struct", "array", "collections", "casioplot", "kandinsky", "ion"}
OPERATORS = "+-*/%=<>|&^~"

# Build punctuation at runtime so QSTR-safe spellings never leak to hardware.
_SYMBOL_CODES = (95, 46, 44, 58, 59, 33, 63, 64, 35, 36, 37, 38, 42, 126,
                 40, 41, 91, 93, 123, 125, 61, 43, 45, 47, 92, 124, 94, 60,
                 62, 39, 34, 96)
SYMBOLS = tuple(chr(code) for code in _SYMBOL_CODES)


def themes():
    return THEME_NAMES


def _gint():
    import gint
    return gint


def _is_alpha(ch):
    return len(ch) == 1 and (("a" <= ch <= "z") or ("A" <= ch <= "Z"))


def _is_digit(ch):
    return len(ch) == 1 and "0" <= ch <= "9"


def _is_alnum(ch):
    return _is_alpha(ch) or _is_digit(ch)


def _exists(path):
    try:
        os.stat(path)
        return True
    except OSError as exc:
        if exc.args and exc.args[0] == errno.ENOENT:
            return False
        raise


def _unused_filename(filename):
    """Return filename, or a numbered sibling, without overwriting a file."""
    filename = str(filename or "new.py")
    if not _exists(filename):
        return filename
    slash = filename.rfind("/")
    folder = filename[:slash + 1] if slash >= 0 else ""
    leaf = filename[slash + 1:]
    dot = leaf.rfind(".")
    if dot > 0:
        stem, suffix = leaf[:dot], leaf[dot:]
    else:
        stem, suffix = leaf, ""
    for number in range(1, 1000):
        candidate = folder + stem + "_" + str(number) + suffix
        if not _exists(candidate):
            return candidate
    raise OSError("No unused filename")


class _KeyReader:
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


def _maps(g):
    base = {
        g.KEY_0:"0", g.KEY_1:"1", g.KEY_2:"2", g.KEY_3:"3", g.KEY_4:"4", g.KEY_5:"5", g.KEY_6:"6", g.KEY_7:"7", g.KEY_8:"8", g.KEY_9:"9",
        g.KEY_DOT:".", g.KEY_ADD:"+", g.KEY_SUB:"-", g.KEY_MUL:"*", g.KEY_DIV:"/", g.KEY_LEFTPAR:"(", g.KEY_RIGHTPAR:")", g.KEY_COMMA:",", g.KEY_NEG:" ", g.KEY_EQUALS:"="
    }
    alpha = {
        g.KEY_XOT:"a", g.KEY_LOG:"b", g.KEY_LN:"c", g.KEY_SIN:"d", g.KEY_COS:"e", g.KEY_TAN:"f", g.KEY_FRAC:"g", g.KEY_FD:"h", g.KEY_LEFTPAR:"i", g.KEY_RIGHTPAR:"j", g.KEY_COMMA:"k", g.KEY_ARROW:"l",
        g.KEY_7:"m", g.KEY_8:"n", g.KEY_9:"o", g.KEY_4:"p", g.KEY_5:"q", g.KEY_6:"r", g.KEY_MUL:"s", g.KEY_DIV:"t", g.KEY_1:"u", g.KEY_2:"v", g.KEY_3:"w", g.KEY_ADD:"x", g.KEY_SUB:"y", g.KEY_0:"z", g.KEY_DOT:" ", g.KEY_EXP:'"', g.KEY_VARS:"_", g.KEY_NEG:" "
    }
    shift = {g.KEY_MUL:"{", g.KEY_DIV:"}", g.KEY_ADD:"[", g.KEY_SUB:"]", g.KEY_DOT:"=", g.KEY_0:":", g.KEY_EXP:"3.14159"}
    return base, alpha, shift


class Editor:
    def __init__(self, filename="new.py", theme=DEFAULT_THEME):
        self.g = _gint()
        self._keys = _KeyReader(self.g)
        self.base_map, self.alpha_map, self.shift_map = _maps(self.g)
        self.filename = str(filename or "new.py")
        self.lines = [""]
        self.cx = 0
        self.cy = 0
        self.goal_x = 0
        self.scroll_x = 0
        self.scroll_y = 0
        self.mode = "NORMAL"
        self.alpha_mode = 0
        self.shift_active = False
        self.clipboard = ""
        self.sel_start = None
        self.last_search = ""
        self.dirty = False
        self.load_failed = False
        self.msg = ""
        self.theme_name = theme if theme in THEMES else DEFAULT_THEME
        self.palette = THEMES[self.theme_name]
        self.font_name = DEFAULT_FONT
        self.apply_font(self.font_name)
        self.load_file(self.filename, allow_new=True)

    def set_theme(self, name):
        if name in THEMES:
            self.theme_name = name
            self.palette = THEMES[name]
            self.msg = name

    def _select_body_font(self):
        builtin = FONT_CONFIG[self.font_name][0]
        return self.g.dfont_builtin(builtin)

    def _select_ui_font(self):
        return self.g.dfont_builtin(UI_FONT)

    def apply_font(self, name):
        global FONT_W, FONT_H, MAX_ROWS, MAX_COLS
        if name not in FONT_CONFIG:
            return False
        builtin, fallback_width, fallback_height = FONT_CONFIG[name]
        metrics = self.g.dfont_builtin(builtin)
        try:
            FONT_W = max(1, int(metrics[0]))
            FONT_H = max(1, int(metrics[1]))
        except Exception:
            FONT_W, FONT_H = fallback_width, fallback_height
        MAX_ROWS = max(1, BODY_H // FONT_H)
        MAX_COLS = max(4, (SCREEN_W - TEXT_X) // FONT_W)
        self.font_name = name
        self._ensure_visible()
        self.msg = name
        return True

    def _text_size(self, text):
        if not text:
            return 0, FONT_H
        try:
            width, height = self.g.dsize(text)
            return max(0, int(width)), max(1, int(height))
        except Exception:
            return len(text) * FONT_W, FONT_H

    def _text_width(self, text):
        return self._text_size(text)[0]

    def _text_advance(self, text):
        # gint dsize excludes the final inter-glyph gap. Include that gap when
        # continuing a separately colored token or positioning the cursor.
        if not text:
            return 0
        return self._text_width(text + " ") - self._text_width(" ")

    def _fit_text(self, text, width):
        text = str(text)
        low, high = 0, len(text)
        while low < high:
            middle = (low + high + 1) // 2
            if self._text_width(text[:middle]) <= width:
                low = middle
            else:
                high = middle - 1
        return text[:low]

    def _fit_tail(self, text, width):
        text = str(text)
        low, high = 0, len(text)
        while low < high:
            middle = (low + high) // 2
            if self._text_width(text[middle:]) <= width:
                high = middle
            else:
                low = middle + 1
        return text[low:]

    def resolve_char(self, key):
        if self.alpha_mode:
            char = self.alpha_map.get(key, self.base_map.get(key))
            if char and ((self.alpha_mode == 2) != self.shift_active):
                return char.upper()
            return char
        if self.shift_active and key in self.shift_map:
            return self.shift_map[key]
        return self.base_map.get(key)

    def _input_mode(self):
        if self.alpha_mode:
            return "A" if ((self.alpha_mode == 2) != self.shift_active) else "a"
        return "S" if self.shift_active else "1"

    def _reset_view(self):
        self.cx = 0
        self.cy = 0
        self.goal_x = 0
        self.scroll_x = 0
        self.scroll_y = 0
        self.sel_start = None
        self.mode = "NORMAL"

    def load_file(self, filename=None, allow_new=False):
        """Load a file atomically; leave the current buffer intact on error."""
        candidate = str(filename if filename is not None else self.filename).strip()
        if not candidate:
            self.msg = "Name error"
            return False
        try:
            stat_result = os.stat(candidate)
        except OSError as exc:
            if allow_new and exc.args and exc.args[0] == errno.ENOENT:
                self.filename = candidate
                self.lines = [""]
                self._reset_view()
                self.dirty = False
                self.load_failed = False
                self.msg = "New"
                return True
            self.msg = "Open " + str(exc)[:18]
            if allow_new:
                self.load_failed = True
            return False
        try:
            if stat_result[6] > MAX_EDIT_BYTES:
                if allow_new: self.load_failed = True
                self.msg = "File too large"
                return False
            pyperm.require_read(candidate)
            with open(candidate, "r") as source:
                text = source.read(MAX_EDIT_BYTES + 1)
            if len(text) > MAX_EDIT_BYTES or text.count("\n") >= MAX_EDIT_LINES:
                if allow_new: self.load_failed = True
                self.msg = "File too large"
                return False
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            new_lines = text.split("\n") if text else [""]
        except Exception as exc:
            if allow_new: self.load_failed = True
            self.msg = "Open " + str(exc)[:18]
            gc.collect()
            return False
        self.filename = candidate
        self.load_failed = False
        self.lines = new_lines
        self._reset_view()
        self.dirty = False
        self.msg = "Read only" if not pyperm.writable(candidate) else "Loaded"
        gc.collect()
        return True

    def start_new(self, filename):
        candidate = str(filename or "").strip()
        if not candidate:
            self.msg = "Name error"
            return False
        if _exists(candidate):
            self.msg = "Already exists"
            return False
        self.filename = candidate
        self.load_failed = False
        self.lines = [""]
        self._reset_view()
        self.dirty = True
        self.msg = "New"
        return True

    def save_file(self, filename=None):
        if self.load_failed:
            self.msg = "Open failed; use New"
            return False
        candidate = str(filename if filename is not None else self.filename).strip()
        if not candidate:
            self.msg = "Name error"
            return False
        temporary = None
        backup = None
        try:
            pyperm.require_write(candidate)
            parent = candidate.rsplit("/", 1)[0] if "/" in candidate else "."
            pyperm.require_write(parent or "/")
            temporary = _unused_filename(candidate + ".pu-tmp")
            with open(temporary, "w") as target:
                for index, line in enumerate(self.lines):
                    if index: target.write("\n")
                    target.write(line)
                target.flush()
            if _exists(candidate):
                backup = _unused_filename(candidate + ".pu-backup")
                os.rename(candidate, backup)
            try:
                os.rename(temporary, candidate)
                temporary = None
            except Exception:
                if backup is not None:
                    os.rename(backup, candidate)
                    backup = None
                raise
            self.filename = candidate
            self.dirty = False
            self.msg = "Saved"
            if backup is not None:
                try:
                    os.remove(backup)
                except OSError:
                    self.msg = "Saved; backup kept"
            return True
        except Exception as exc:
            self.msg = "Save " + str(exc)[:18]
            return False
        finally:
            if temporary is not None:
                try:
                    os.remove(temporary)
                except OSError:
                    pass

    def _token_color(self, token, first):
        palette = self.palette
        if first == "#": return palette[COMMENT]
        if first in "\"'": return palette[STRING]
        if first == "@": return palette[DECORATOR]
        if token in KEYWORDS: return palette[KEYWORD]
        if token in BUILTINS: return palette[BUILTIN]
        if token in TYPES: return palette[TYPE]
        if token in MODULES: return palette[BUILTIN]
        if token and _is_digit(token[0]): return palette[NUMBER]
        if first in OPERATORS: return palette[KEYWORD]
        return palette[FG]

    def _quote_closes(self, text, index, start):
        slashes = 0
        probe = index - 1
        while probe >= start and text[probe] == "\\":
            slashes += 1
            probe -= 1
        return slashes % 2 == 0

    def draw_line(self, text, y, line_index):
        g = self.g
        if self.scroll_x >= len(text):
            return
        i = self.scroll_x
        x = TEXT_X
        # More than 256 proportional glyphs cannot fit on this display and a
        # bound avoids scanning a pathological one-line file on every frame.
        limit = min(len(text), self.scroll_x + 256)
        while i < limit and x < SCREEN_W:
            char = text[i]
            j = i + 1
            if char == "#":
                j = limit
            elif char in "\"'":
                while j < limit:
                    if text[j] == char and self._quote_closes(text, j, i):
                        j += 1
                        break
                    j += 1
            elif _is_alpha(char) or char == "_":
                while j < limit and (_is_alnum(text[j]) or text[j] == "_"):
                    j += 1
            elif _is_digit(char):
                while j < limit and (_is_digit(text[j]) or text[j] == "."):
                    j += 1
            elif char == "@":
                while j < limit and (_is_alnum(text[j]) or text[j] in "_."):
                    j += 1
            token = text[i:j]
            color = self._token_color(token, char)
            if self.mode == "VISUAL" and self.sel_start:
                first_pos = self.sel_start
                last_pos = (self.cy, self.cx)
                if first_pos > last_pos:
                    first_pos, last_pos = last_pos, first_pos
                for offset, glyph in enumerate(token):
                    absolute = i + offset
                    glyph_width = max(1, self._text_advance(glyph))
                    selected = first_pos <= (line_index, absolute) <= last_pos
                    if selected:
                        g.drect(x, y, x + glyph_width - 1, y + FONT_H - 1, self.palette[SEL_BG])
                    g.dtext(x, y, self.palette[SEL_FG] if selected else color, glyph)
                    x += glyph_width
                    if x >= SCREEN_W:
                        break
            else:
                g.dtext(x, y, color, token)
                x += self._text_advance(token)
            i = j

    def _ensure_visible(self):
        if not self.lines:
            self.lines = [""]
        self.cy = max(0, min(len(self.lines) - 1, self.cy))
        self.cx = max(0, min(len(self.lines[self.cy]), self.cx))
        if self.cy < self.scroll_y:
            self.scroll_y = self.cy
        if self.cy >= self.scroll_y + MAX_ROWS:
            self.scroll_y = self.cy - MAX_ROWS + 1
        self.scroll_y = max(0, self.scroll_y)
        if self.cx < self.scroll_x:
            self.scroll_x = self.cx
        line = self.lines[self.cy]
        available = SCREEN_W - TEXT_X - 3
        low, high = self.scroll_x, self.cx
        while low < high:
            middle = (low + high) // 2
            if self._text_advance(line[middle:self.cx]) > available:
                low = middle + 1
            else:
                high = middle
        self.scroll_x = low
        self.scroll_x = max(0, min(self.scroll_x, self.cx))

    def draw(self):
        g = self.g
        palette = self.palette
        self._select_body_font()
        self._ensure_visible()
        g.dclear(palette[BG])
        for row in range(MAX_ROWS):
            index = self.scroll_y + row
            if index >= len(self.lines):
                break
            self.draw_line(self.lines[index], row * FONT_H, index)

        row = self.cy - self.scroll_y
        if 0 <= row < MAX_ROWS:
            line = self.lines[self.cy]
            x = TEXT_X + self._text_advance(line[self.scroll_x:self.cx])
            y = row * FONT_H
            if x < SCREEN_W:
                cursor_char = line[self.cx:self.cx + 1] or " "
                cursor_width = max(2, self._text_width(cursor_char))
                if self.mode == "INSERT":
                    g.drect(x, y, x + 1, y + FONT_H - 1, palette[FG])
                else:
                    g.drect_border(x, y, min(SCREEN_W - 1, x + cursor_width - 1),
                                   y + FONT_H - 1, getattr(g, "C_NONE", -1), 1, palette[FG])

        y_info = SCREEN_H - NAV_H - INFO_H
        y_nav = SCREEN_H - NAV_H
        self._select_ui_font()
        g.drect(0, y_info, SCREEN_W - 1, y_nav - 1, palette[BG])
        g.drect(0, y_nav, SCREEN_W - 1, SCREEN_H - 1, palette[BAR])
        mode = self._input_mode()
        changed = "*" if self.dirty else ""
        info = "%s [%s] %d:%d %s%s %s" % (
            self.mode, mode, self.cy + 1, self.cx + 1,
            self.filename, changed, self.msg)
        g.dtext(2, y_info + 1, palette[FG], self._fit_text(info, SCREEN_W - 4))
        labels = ("Run", "Save", "New", "Open", "Find", "Sym")
        for index, label in enumerate(labels):
            x1 = index * 66
            x2 = SCREEN_W - 1 if index == 5 else x1 + 65
            g.drect_border(x1, y_nav, x2, SCREEN_H - 1,
                           palette[BAR], 1, palette[BORDER])
            text = "F%d %s" % (index + 1, label)
            text = self._fit_text(text, x2 - x1 - 4)
            width = self._text_width(text)
            g.dtext(x1 + max(2, (x2 - x1 + 1 - width) // 2),
                    y_nav + 1, palette[BAR_FG], text)
        self._select_body_font()
        g.dupdate()

    def popup(self, title, items):
        """Small editor-owned popup that keeps using the safe raw-key path."""
        g = self.g
        palette = self.palette
        items = tuple(items)
        if not items:
            return None
        selected = 0
        top = 0
        visible = 9
        import pythonultra
        border = pythonultra.menu_border()
        try:
            while True:
                self._select_ui_font()
                g.dclear(palette[BG])
                g.drect_border(0, 0, SCREEN_W - 1, SCREEN_H - 1,
                               palette[BG], 2, border)
                g.drect(2, 2, SCREEN_W - 3, 16, palette[BAR])
                g.dtext(4, 3, palette[BAR_FG], self._fit_text(title, SCREEN_W - 8))
                if selected < top:
                    top = selected
                if selected >= top + visible:
                    top = selected - visible + 1
                for row in range(visible):
                    index = top + row
                    if index >= len(items):
                        break
                    y = 20 + row * 20
                    if index == selected:
                        g.drect(4, y - 1, SCREEN_W - 5, y + 16, palette[SEL_BG])
                    text = self._fit_text(str(items[index]), SCREEN_W - 18)
                    color = palette[SEL_FG] if index == selected else palette[FG]
                    g.dtext(10, y + 2, color, text)
                g.dtext(4, SCREEN_H - 12, palette[FG], "EXE select   EXIT cancel")
                g.dupdate()
                key = self._keys.read()
                if key == g.KEY_UP:
                    selected = (selected - 1) % len(items)
                elif key == g.KEY_DOWN:
                    selected = (selected + 1) % len(items)
                elif key == g.KEY_EXE:
                    return items[selected]
                elif key == g.KEY_EXIT:
                    return None
        finally:
            self._select_body_font()

    def input_bar(self, prompt, initial=""):
        g = self.g
        text = str(initial)
        import pythonultra
        border = pythonultra.menu_border()
        try:
            while True:
                self.draw()
                palette = self.palette
                self._select_ui_font()
                g.drect(20, 76, 376, 121, palette[BG])
                g.drect_border(20, 76, 376, 121, palette[BG], 2, border)
                g.dtext(28, 83, palette[FG], self._fit_text(str(prompt), 340))
                shown = self._fit_tail(text + "_", 340)
                g.dtext(28, 101, palette[FG], shown)
                g.dupdate()
                key = self._keys.read()
                if key == g.KEY_EXIT:
                    return None
                if key == g.KEY_EXE:
                    return text
                if key == g.KEY_SHIFT:
                    self.shift_active = not self.shift_active
                    continue
                if key == g.KEY_ALPHA:
                    self.alpha_mode = 2 if self.shift_active else (0 if self.alpha_mode else 1)
                    self.shift_active = False
                    continue
                if key == g.KEY_F6 or (self.shift_active and key == g.KEY_DEL):
                    self.shift_active = False
                    symbol = self.popup("Symbols", SYMBOLS)
                    if symbol:
                        text += symbol
                    continue
                if self.shift_active and key == g.KEY_VARS:
                    self.shift_active = False
                    self.style_menu()
                    continue
                if key == g.KEY_DEL:
                    text = text[:-1]
                    continue
                char = self.resolve_char(key)
                if char:
                    text += char
                if self.shift_active:
                    self.shift_active = False
        finally:
            self._select_body_font()

    def move(self, dy, dx):
        if dy:
            self.cy = max(0, min(len(self.lines) - 1, self.cy + dy))
            self.cx = min(len(self.lines[self.cy]), self.goal_x)
        else:
            self.cx = max(0, min(len(self.lines[self.cy]), self.cx + dx))
            self.goal_x = self.cx
        self._ensure_visible()

    def insert(self, text):
        if not text:
            return
        text = str(text).replace("\r\n", "\n").replace("\r", "\n")
        if (sum(len(line) + 1 for line in self.lines) + len(text) > MAX_EDIT_BYTES
                or len(self.lines) + text.count("\n") > MAX_EDIT_LINES):
            self.msg = "Editor size limit"
            return
        line = self.lines[self.cy]
        parts = text.split("\n")
        if len(parts) == 1:
            self.lines[self.cy] = line[:self.cx] + text + line[self.cx:]
            self.cx += len(text)
        else:
            before = line[:self.cx]
            after = line[self.cx:]
            self.lines[self.cy] = before + parts[0]
            for offset, middle in enumerate(parts[1:-1], 1):
                self.lines.insert(self.cy + offset, middle)
            self.lines.insert(self.cy + len(parts) - 1, parts[-1] + after)
            self.cy += len(parts) - 1
            self.cx = len(parts[-1])
        self.goal_x = self.cx
        self.dirty = True
        self._ensure_visible()

    def backspace(self):
        if self.cx > 0:
            line = self.lines[self.cy]
            self.lines[self.cy] = line[:self.cx - 1] + line[self.cx:]
            self.cx -= 1
            self.dirty = True
        elif self.cy > 0:
            previous = self.lines[self.cy - 1]
            current = self.lines.pop(self.cy)
            self.cy -= 1
            self.cx = len(previous)
            self.lines[self.cy] = previous + current
            self.dirty = True
        self.goal_x = self.cx
        self._ensure_visible()

    def newline(self):
        if len(self.lines) >= MAX_EDIT_LINES:
            self.msg = "Editor line limit"
            return
        line = self.lines[self.cy]
        before = line[:self.cx]
        after = line[self.cx:]
        indent = ""
        for char in before:
            if char == " ":
                indent += " "
            else:
                break
        if before.rstrip().endswith(":"):
            indent += "    "
        self.lines[self.cy] = before
        self.lines.insert(self.cy + 1, indent + after)
        self.cy += 1
        self.cx = len(indent)
        self.goal_x = self.cx
        self.dirty = True
        self._ensure_visible()

    def copy_selection(self, cut=False):
        if not self.sel_start:
            return
        first_pos = self.sel_start
        last_pos = (self.cy, self.cx)
        if first_pos > last_pos:
            first_pos, last_pos = last_pos, first_pos
        chunks = []
        for row in range(first_pos[0], last_pos[0] + 1):
            line = self.lines[row]
            left = first_pos[1] if row == first_pos[0] else 0
            right = last_pos[1] + 1 if row == last_pos[0] else len(line)
            chunks.append(line[left:right])
        self.clipboard = "\n".join(chunks)
        if cut:
            head = self.lines[first_pos[0]][:first_pos[1]]
            tail = self.lines[last_pos[0]][last_pos[1] + 1:]
            self.lines[first_pos[0]] = head + tail
            for _ in range(last_pos[0] - first_pos[0]):
                self.lines.pop(first_pos[0] + 1)
            self.cy, self.cx = first_pos
            self.goal_x = self.cx
            self.dirty = True
        self.mode = "NORMAL"
        self.sel_start = None
        self.msg = "Cut" if cut else "Copied"
        self._ensure_visible()

    def find(self):
        query = self.input_bar("Find", self.last_search)
        if not query:
            return
        self.last_search = query
        for offset in range(len(self.lines)):
            row = (self.cy + offset) % len(self.lines)
            start = self.cx + 1 if row == self.cy else 0
            position = self.lines[row].find(query, start)
            if position >= 0:
                self.cy = row
                self.cx = position
                self.goal_x = self.cx
                self.msg = "Found"
                self._ensure_visible()
                return
        # Wrap around the starting line too, including a match at its cursor.
        position = self.lines[self.cy].find(query, 0, self.cx + len(query))
        if position >= 0:
            self.cx = position
            self.goal_x = self.cx
            self.msg = "Found"
            self._ensure_visible()
            return
        self.msg = "Not found"

    def style_menu(self):
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
        import pythonultra
        module = self.popup("Catalog", pythonultra.modules())
        if not module:
            return
        member = self.popup(module, pythonultra.catalog_data(module))
        if member:
            self.insert(pythonultra.catalog_text(module, member))

    def confirm_discard(self):
        if not self.dirty:
            return True
        return self.popup("Unsaved changes", ("Cancel", "Discard")) == "Discard"

    def _new_default(self):
        slash = self.filename.rfind("/")
        folder = self.filename[:slash + 1] if slash >= 0 else ""
        return _unused_filename(folder + "new.py")

    def run_code(self):
        """Save and execute the buffer exactly once; return success."""
        if not self.filename.lower().endswith(".py"):
            self.msg = "Run needs .py"
            return False
        if self.load_failed:
            self.msg = "Open failed"
            return False
        if (self.dirty or not _exists(self.filename)) and not self.save_file():
            return False
        old_path = list(sys.path)
        success = False
        try:
            pyperm.require_read(self.filename)
            folder = self.filename.rsplit("/", 1)[0] if "/" in self.filename else "."
            folder = folder or "/"
            if folder not in sys.path:
                sys.path.insert(0, folder)
            with open(self.filename, "r") as source:
                code = source.read(MAX_EDIT_BYTES + 1)
            if len(code) > MAX_EDIT_BYTES:
                raise ValueError("file too large")
            scope = {"__name__":"__main__", "__file__":self.filename}
            exec(code, scope, scope)
            self.msg = "Run OK"
            success = True
        except Exception as exc:
            print("Editor run error:", repr(exc))
            self.msg = "Run error"
        finally:
            sys.path[:] = old_path
            self._select_body_font()
            gc.collect()
        return success

    def run(self):
        g = self.g
        # Drain the JustUI launcher's release/modifier tail before taking over
        # the global keyboard event queue.
        g.clearevents()
        self._keys.pending[:] = []
        try:
            while True:
                self.draw()
                key = self._keys.read()
                if key in (g.KEY_F1, g.KEY_F2, g.KEY_F3, g.KEY_F4, g.KEY_F5):
                    self.shift_active = False
                if key == g.KEY_F1:
                    if self.run_code():
                        return "run"
                    continue
                if key == g.KEY_F2:
                    self.save_file()
                    continue
                if key == g.KEY_F3:
                    if self.confirm_discard():
                        default = self._new_default()
                        name = self.input_bar("New file", default)
                        if name:
                            self.start_new(name)
                    continue
                if key == g.KEY_F4:
                    if self.confirm_discard():
                        name = self.input_bar("Open", self.filename)
                        if name:
                            self.load_file(name)
                    continue
                if key == g.KEY_F5:
                    self.find()
                    continue
                if key == g.KEY_F6:
                    self.shift_active = False
                    symbol = self.popup("Symbols", SYMBOLS)
                    if symbol:
                        self.insert(symbol)
                        self.mode = "INSERT"
                    continue
                if key == g.KEY_SHIFT:
                    self.shift_active = not self.shift_active
                    continue
                if key == g.KEY_ALPHA:
                    self.alpha_mode = 2 if self.shift_active else (0 if self.alpha_mode else 1)
                    self.shift_active = False
                    continue
                if self.shift_active:
                    if key == g.KEY_VARS:
                        self.shift_active = False
                        self.style_menu()
                        continue
                    if not self.alpha_mode and key == g.KEY_8:
                        self.mode = "VISUAL"
                        self.sel_start = (self.cy, self.cx)
                        self.shift_active = False
                        continue
                    if not self.alpha_mode and key == g.KEY_9:
                        self.insert(self.clipboard)
                        self.shift_active = False
                        continue
                    if not self.alpha_mode and key == g.KEY_4:
                        self.catalog_menu()
                        self.shift_active = False
                        continue
                    if key == g.KEY_DEL:
                        symbol = self.popup("Symbols", SYMBOLS)
                        if symbol:
                            self.insert(symbol)
                        self.shift_active = False
                        continue
                if self.mode == "VISUAL":
                    if key == g.KEY_OPTN:
                        self.copy_selection(False)
                        continue
                    if key == g.KEY_DEL:
                        self.copy_selection(True)
                        continue
                if key == g.KEY_UP:
                    self.move(-1, 0)
                elif key == g.KEY_DOWN:
                    self.move(1, 0)
                elif key == g.KEY_LEFT:
                    self.move(0, -1)
                elif key == g.KEY_RIGHT:
                    self.move(0, 1)
                elif key == g.KEY_OPTN:
                    self.mode = "NORMAL" if self.mode == "INSERT" else "INSERT"
                    self.sel_start = None
                elif key == g.KEY_DEL:
                    if self.mode == "INSERT":
                        self.backspace()
                elif key == g.KEY_EXE:
                    if self.mode != "VISUAL":
                        self.mode = "INSERT"
                        self.newline()
                elif key == g.KEY_EXIT:
                    if self.confirm_discard():
                        return "exit"
                else:
                    char = self.resolve_char(key)
                    if char:
                        if self.mode == "NORMAL":
                            self.mode = "INSERT"
                        if self.mode == "INSERT":
                            self.insert(char)
                if self.shift_active and key not in (g.KEY_SHIFT, g.KEY_ALPHA):
                    self.shift_active = False
        finally:
            g.dfont(None)
            gc.collect()


def open_file(filename, theme=DEFAULT_THEME):
    """Edit an existing file; F1 executes it once before returning."""
    return Editor(filename, theme).run()


def new_file(filename="new.py", theme=DEFAULT_THEME):
    """Open a new unsaved file without overwriting an existing sibling."""
    editor = Editor(_unused_filename(filename), theme)
    if not editor.load_failed:
        editor.dirty = True
        editor.msg = "New"
    return editor.run()
