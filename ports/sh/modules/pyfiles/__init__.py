"""PythonUltra graphical file manager for the fx-CG50."""

import gc
import os
import sys
import pyperm

__version__ = "0.7.0-cg50"

SCREEN_W = 396
SCREEN_H = 224
HEADER_H = 18
NAV_H = 13
ROW_H = 13
VISIBLE = (SCREEN_H - HEADER_H - NAV_H) // ROW_H
COPY_CHUNK = 1024

TEXT_EXTENSIONS = (
    ".py", ".txt", ".md", ".csv", ".json", ".ini", ".cfg", ".log",
    ".xml", ".html", ".css", ".js", ".c", ".h", ".cpp", ".hpp", ".sh",
    ".toml", ".yaml", ".yml", ".rst", ".dat",
)
IMAGE_EXTENSIONS = (".bmp", ".ppm", ".jpg", ".jpeg")


def _gint():
    import gint
    return gint


def _join(folder, name):
    if folder == "/": return "/" + name
    return folder.rstrip("/") + "/" + name


def _parent(folder):
    if not folder or folder == "/": return "/"
    parts = folder.rstrip("/").split("/")
    value = "/".join(parts[:-1])
    return value if value else "/"


def _basename(path):
    return path.rstrip("/").split("/")[-1]


def _is_dir(path):
    return pyperm.is_dir(path)


def _exists(path):
    try:
        os.stat(path); return True
    except OSError:
        return False


def _looks_text(path):
    lower = path.lower()
    if lower.endswith(TEXT_EXTENSIONS): return True
    return "." not in _basename(path)


def _file_type(path):
    lower = path.lower()
    if lower.endswith(".py"): return "Python source"
    if lower.endswith(".zip"): return "ZIP archive"
    if lower.endswith((".jpg", ".jpeg")): return "JPEG image"
    if lower.endswith(".bmp"): return "BMP image"
    if lower.endswith(".ppm"): return "PPM image"
    if lower.endswith((".txt", ".md", ".log", ".rst")): return "Text file"
    if lower.endswith(".csv"): return "CSV data"
    if lower.endswith(".json"): return "JSON data"
    if lower.endswith((".c", ".h", ".cpp", ".hpp")): return "C/C++ source"
    if lower.endswith((".html", ".css", ".js")): return "Web source"
    if _looks_text(path): return "Text file"
    return "File"


def _file_size(path):
    try: return os.stat(path)[6]
    except OSError: return 0


def _mode_string(path):
    try: return "%03o" % pyperm.get_mode(path)
    except Exception: return "---"


def _modified_text(value):
    # The calculator filesystem may not supply mtime. Do not invent dates
    # for unset fields or display arbitrary integer data as a real timestamp.
    try:
        if not value or value < 0 or value > 0xffffffff:
            return "Unavailable"
        import time
        stamp = time.localtime(value)
        if not 1980 <= stamp[0] <= 2106:
            return "Unavailable"
        return "%04d-%02d-%02d %02d:%02d:%02d" % stamp[:6]
    except (AttributeError, ValueError, TypeError, OverflowError):
        return "Unavailable"


def _remove_tree(path):
    """Best-effort cleanup used only for destinations created by copy."""
    try:
        if _is_dir(path):
            for name in os.listdir(path):
                _remove_tree(_join(path, name))
            os.rmdir(path)
        elif _exists(path):
            os.remove(path)
        pyperm.remove(path)
    except Exception:
        pass


def _copy_file(src, dst):
    pyperm.require_read(src)
    mode = pyperm.get_mode(src, False)
    try:
        with open(src, "rb") as source:
            with open(dst, "wb") as target:
                while True:
                    chunk = source.read(COPY_CHUNK)
                    if not chunk: break
                    target.write(chunk)
        try: pyperm.chmod(dst, mode)
        except Exception: pass
    except Exception:
        _remove_tree(dst)
        raise


def _copy_tree(src, dst):
    pyperm.require_read(src)
    mode = pyperm.get_mode(src, True)
    try:
        os.mkdir(dst)
        try: pyperm.chmod(dst, mode)
        except Exception: pass
        for name in os.listdir(src):
            child_src = _join(src, name)
            child_dst = _join(dst, name)
            if _is_dir(child_src): _copy_tree(child_src, child_dst)
            else: _copy_file(child_src, child_dst)
    except Exception:
        _remove_tree(dst)
        raise


class Browser:
    def __init__(self, folder="/", theme="GitHub Dark"):
        import pyeditor
        self.g = _gint()
        self.pyeditor = pyeditor
        self.folder = folder or "/"
        self.theme_name = theme if theme in pyeditor.THEMES else pyeditor.DEFAULT_THEME
        self.palette = pyeditor.THEMES[self.theme_name]
        self.entries = []
        self.selected = 0
        self.scroll = 0
        self.msg = ""
        self.marked = set()
        self.sort_mode = "Name A-Z"
        self.last_search = ""
        self.clipboard = []
        self.clipboard_mode = None
        self.refresh()

    def refresh(self):
        try: names = os.listdir(self.folder)
        except OSError as exc:
            names = []; self.msg = "List " + str(exc)[:14]
        dirs, files = [], []
        for name in names:
            (dirs if _is_dir(_join(self.folder, name)) else files).append(name)
        if self.sort_mode == "Type":
            dirs.sort()
            files.sort(key=lambda name: (_file_type(_join(self.folder, name)).lower(), name.lower()))
        elif self.sort_mode == "Size small-large":
            dirs.sort()
            files.sort(key=lambda name: (_file_size(_join(self.folder, name)), name.lower()))
        elif self.sort_mode == "Size large-small":
            dirs.sort()
            files.sort(key=lambda name: (_file_size(_join(self.folder, name)), name.lower()), reverse=True)
        else:
            reverse = self.sort_mode == "Name Z-A"
            dirs.sort(reverse=reverse); files.sort(reverse=reverse)
        if self.sort_mode == "Files first":
            self.entries = [(name, False) for name in files] + [(name, True) for name in dirs]
        else:
            self.entries = [(name, True) for name in dirs] + [(name, False) for name in files]
        kept = set()
        for name in self.marked:
            if name in names: kept.add(name)
        self.marked = kept
        if self.entries: self.selected = max(0, min(self.selected, len(self.entries) - 1))
        else: self.selected = 0
        self.scroll = max(0, min(self.scroll, max(0, len(self.entries) - VISIBLE)))
        gc.collect()

    def selected_entry(self):
        return self.entries[self.selected] if self.entries else None

    def selected_path(self):
        entry = self.selected_entry()
        return _join(self.folder, entry[0]) if entry else None

    def selection_targets(self):
        targets = []
        if self.marked:
            for name, is_dir in self.entries:
                if name in self.marked:
                    targets.append((_join(self.folder, name), is_dir))
        else:
            entry = self.selected_entry()
            if entry:
                targets.append((_join(self.folder, entry[0]), entry[1]))
        return targets

    def draw_softkeys(self, labels):
        g, p = self.g, self.palette
        y = SCREEN_H - NAV_H
        for i in range(6):
            x0 = i * 66
            x1 = min(SCREEN_W - 1, x0 + 65)
            g.drect(x0, y, x1, SCREEN_H - 1, p[2])
            g.drect_border(x0 + 1, y, x1 - 1, SCREEN_H - 1, p[13], 1, p[2])
            label = labels[i] if i < len(labels) else ""
            if label:
                label = label[:7]
                x = x0 + max(3, (64 - len(label) * 8) // 2)
                g.dtext(x, y + 1, p[3], label)

    def draw(self):
        g, p = self.g, self.palette
        g.dclear(p[0])
        g.drect(0, 0, SCREEN_W - 1, HEADER_H - 1, p[2])
        title = "Files " + self.folder
        if self.msg: title += "  " + self.msg
        selected = self.selected_entry()
        hint = "EXE:INFO"
        if selected and selected[1]: hint = "EXE:OPEN"
        if self.marked:
            hint = str(len(self.marked)) + " SELECT"
        elif self.clipboard_mode:
            hint = self.clipboard_mode.upper() + " " + str(len(self.clipboard))
        g.dtext(4, 3, p[3], title[:35])
        g.dtext(314, 3, p[3], hint[:10])
        if self.selected < self.scroll: self.scroll = self.selected
        if self.selected >= self.scroll + VISIBLE: self.scroll = self.selected - VISIBLE + 1
        for row in range(VISIBLE):
            idx = self.scroll + row
            if idx >= len(self.entries): break
            name, is_dir = self.entries[idx]
            y = HEADER_H + row * ROW_H
            sel = idx == self.selected
            bg = p[4] if sel else p[0]
            fg = p[5] if sel else p[1]
            g.drect(2, y, SCREEN_W - 3, y + ROW_H - 1, bg)
            if name in self.marked:
                marker = "[*] "
            else:
                marker = "[D] " if is_dir else ("[Z] " if name.lower().endswith(".zip") else "    ")
            g.dtext(6, y + 1, fg, (marker + name)[:46])
        self.draw_softkeys(("SELECT", "SEQ", "SEARCH", "NEW", "RENAME", "MORE"))
        g.dupdate()

    def popup(self, title, items):
        import pythonultra
        dark = self.theme_name not in ("GitHub Light", "PythonUltra Light")
        return pythonultra.popup(title, tuple(items), dark)

    def input_bar(self, prompt, initial=""):
        g = self.g
        base, alpha, shift = self.pyeditor._maps(g)
        text = initial; alpha_mode = 0; shift_on = False
        while True:
            self.draw(); p = self.palette
            g.drect(18, 78, 378, 116, p[0])
            g.drect_border(18, 78, 378, 116, p[13], 2, p[0])
            mod = "A" if alpha_mode == 2 else ("a" if alpha_mode else "1")
            g.dtext(26, 88, p[1], ("[" + mod + "] " + prompt + ": " + text + "_")[-44:])
            g.dupdate(); key = self.pyeditor._raw_key(g)
            if key == g.KEY_EXIT: return None
            if key == g.KEY_EXE: return text
            if key == g.KEY_SHIFT: shift_on = not shift_on; continue
            if key == g.KEY_ALPHA:
                alpha_mode = 2 if shift_on else (0 if alpha_mode else 1); shift_on = False; continue
            if key == g.KEY_DEL:
                if shift_on:
                    symbol = self.popup("Symbols", self.pyeditor.SYMBOLS)
                    if symbol: text += symbol
                    shift_on = False
                else: text = text[:-1]
                continue
            if shift_on and key in shift: char = shift[key]
            elif alpha_mode:
                char = alpha.get(key, base.get(key))
                if char and alpha_mode == 2: char = char.upper()
            else: char = base.get(key)
            if char: text += char
            if shift_on: shift_on = False

    def toggle_selected(self):
        entry = self.selected_entry()
        if not entry: return
        name = entry[0]
        if name in self.marked:
            self.marked.remove(name)
        else:
            self.marked.add(name)
        self.msg = str(len(self.marked)) + " selected" if self.marked else "Selection clear"

    def sequence_menu(self):
        choice = self.popup("Sequence", (
            "Name A-Z", "Name Z-A", "Type", "Size small-large", "Size large-small",
            "Files first", "Cancel"))
        if not choice or choice == "Cancel": return
        self.sort_mode = choice
        self.selected = self.scroll = 0
        self.msg = choice
        self.refresh()

    def search_menu(self):
        query = self.input_bar("Search", self.last_search)
        if query is None: return
        query = query.strip()
        if not query:
            self.msg = "Search empty"; return
        self.last_search = query
        q = query.lower()
        matches = []
        for name, is_dir in self.entries:
            if q in name.lower(): matches.append(name)
        if not matches:
            self.msg = "No matches"; return
        choice = self.popup("Search " + query[:18], matches)
        if not choice: return
        for idx, entry in enumerate(self.entries):
            if entry[0] == choice:
                self.selected = idx
                self.scroll = max(0, min(idx, max(0, len(self.entries) - VISIBLE)))
                self.msg = str(len(matches)) + " match" + ("es" if len(matches) != 1 else "")
                return

    def text_viewer(self, path):
        g, p = self.g, self.palette
        try:
            pyperm.require_read(path)
            with open(path, "r") as f: text = f.read(12288)
        except Exception as exc:
            self.msg = "Open " + str(exc)[:12]; return
        lines = text.split("\n") if text else [""]
        top = 0
        rows = 17
        while True:
            g.dclear(p[0])
            g.drect(0, 0, SCREEN_W - 1, HEADER_H - 1, p[2])
            g.dtext(4, 3, p[3], ("OPEN " + _basename(path))[:44])
            for row in range(rows):
                idx = top + row
                if idx >= len(lines): break
                g.dtext(4, HEADER_H + row * 11, p[1], lines[idx][:48])
            self.draw_softkeys(("", "", "", "", "", "BACK"))
            g.dupdate(); key = g.getkey().key
            if key in (g.KEY_EXIT, g.KEY_F6, g.KEY_LEFT): return
            if key == g.KEY_UP: top = max(0, top - 1)
            elif key == g.KEY_DOWN: top = min(max(0, len(lines) - rows), top + 1)
            elif key == g.KEY_ADD: top = min(max(0, len(lines) - rows), top + rows)
            elif key == g.KEY_SUB: top = max(0, top - rows)

    def _draw_file_info(self, path, st):
        g, p = self.g, self.palette
        lower = path.lower()
        action = "RUN" if lower.endswith(".py") else ("UNZIP" if lower.endswith(".zip") else "PERM")
        g.dclear(p[0])
        g.drect(0, 0, SCREEN_W - 1, HEADER_H - 1, p[2])
        g.dtext(4, 3, p[3], "File information")
        g.dtext(8, 28, p[3], "Filename:")
        g.dtext(8, 41, p[1], _basename(path)[:42])
        g.dtext(8, 59, p[3], "Full file path:")
        g.dtext(8, 72, p[1], path[:46])
        g.dtext(8, 91, p[3], "File type:")
        g.dtext(116, 91, p[1], _file_type(path)[:29])
        g.dtext(8, 108, p[3], "File size:")
        g.dtext(116, 108, p[1], str(st[6]) + " bytes")
        g.dtext(8, 125, p[3], "Permissions:")
        g.dtext(116, 125, p[1], _mode_string(path))
        if len(st) > 8:
            g.dtext(8, 142, p[3], "Modified:")
            g.dtext(116, 142, p[1], _modified_text(st[8]))
        self.draw_softkeys(("OPEN", "EDIT", "COMP", action, "", "CALC"))

    def checksum_ui(self, path, st=None):
        g, p = self.g, self.palette
        if st is None:
            try: st = os.stat(path)
            except OSError:
                self.msg = "Stat error"; return
        try:
            import checksum
            self._draw_file_info(path, st)
            g.drect(82, 72, 314, 108, p[0])
            g.drect_border(82, 72, 314, 108, p[13], 2, p[0])
            g.dtext(98, 84, p[1], "Calculating checksums...")
            g.dupdate()
            sha256 = checksum.sha256_file(path)
            sha1 = checksum.sha1_file(path)
        except Exception as exc:
            print("Checksum error:", repr(exc)); self.msg = "Hash error"; return
        while True:
            self._draw_file_info(path, st)
            g.drect(64, 45, 369, 184, p[2])
            g.drect_border(58, 39, 363, 178, p[13], 2, p[0])
            g.drect_border(62, 43, 359, 174, p[13], 1, p[0])
            g.dtext(70, 52, p[1], "SHA-256 checksum:")
            g.dtext(70, 67, p[1], sha256[:32])
            g.dtext(70, 80, p[1], sha256[32:64])
            g.dtext(70, 103, p[1], "SHA-1 checksum:")
            g.dtext(70, 118, p[1], sha1[:32])
            g.dtext(70, 131, p[1], sha1[32:40])
            g.dtext(124, 153, p[1], "Press: [EXIT]")
            g.dupdate(); key = g.getkey().key
            if key in (g.KEY_EXIT, g.KEY_F6, g.KEY_LEFT): break
        self.msg = "Hashes OK"

    def file_info(self, path):
        g = self.g
        try: st = os.stat(path)
        except OSError as exc:
            self.msg = "Stat " + str(exc)[:12]; return
        lower = path.lower()
        while True:
            self._draw_file_info(path, st)
            g.dupdate(); key = g.getkey().key
            if key == g.KEY_F1:
                if _looks_text(path): self.text_viewer(path)
                elif lower.endswith(IMAGE_EXTENSIONS):
                    self.msg = "Image preview next"; return
                else:
                    self.msg = "No viewer"; return
            elif key == g.KEY_F2:
                self.edit_file(path); return
            elif key == g.KEY_F3:
                self.compress_selected(path); return
            elif key == g.KEY_F4:
                if lower.endswith(".py"): self.run_file(path); return
                if lower.endswith(".zip"): self.extract_selected(path); return
                self.permission_menu(path)
                try: st = os.stat(path)
                except OSError: return
            elif key == g.KEY_F6:
                self.checksum_ui(path, st)
            elif key in (g.KEY_EXIT, g.KEY_LEFT): return

    def enter_selected(self):
        entry = self.selected_entry()
        if not entry: return
        name, is_dir = entry; path = _join(self.folder, name)
        if is_dir:
            self.folder = path
            self.selected = self.scroll = 0
            self.marked.clear()
            self.msg = ""
            self.refresh()
            return
        self.file_info(path)

    def run_file(self, path=None):
        path = path or self.selected_path()
        if not path or _is_dir(path) or not path.lower().endswith(".py"):
            self.msg = "Run needs .py"; return
        old_path = list(sys.path)
        try:
            pyperm.require_read(path)
            folder = path.rsplit("/", 1)[0] or "/"
            if folder not in sys.path: sys.path.insert(0, folder)
            with open(path, "r") as f: code = f.read()
            scope = {"__name__":"__main__", "__file__":path}
            exec(code, scope, scope); self.msg = "Run OK"
        except Exception as exc:
            print("File run error:", repr(exc)); self.msg = "Run error"
        finally:
            sys.path[:] = old_path; gc.collect()

    def edit_file(self, path=None):
        path = path or self.selected_path()
        if not path or _is_dir(path): self.msg = "Select file"; return
        if not _looks_text(path):
            if self.popup("Unknown/binary type", ("Edit as text", "Cancel")) != "Edit as text": return
        try:
            pyperm.require_read(path)
            # The editor executes F1/Run itself. Do not run the script a second
            # time when control returns to Files.
            self.pyeditor.open_file(path, self.theme_name)
            self.refresh()
        except Exception as exc: self.msg = "Edit " + str(exc)[:12]

    def open_editor(self):
        try:
            self.pyeditor.new_file(_join(self.folder, "new.py"), self.theme_name)
            self.refresh()
        except Exception as exc:
            self.msg = "Editor " + str(exc)[:10]

    def create_new(self):
        kind = self.popup("New", ("File", "Folder", "Cancel"))
        if kind == "File":
            name = self.input_bar("New file", "new.txt")
            if not name: return
            path = _join(self.folder, name)
            if _exists(path): self.msg = "Already exists"; return
            try:
                with open(path, "w") as f: f.write("")
                self.msg = "Created"; self.refresh(); self.edit_file(path)
            except OSError as exc: self.msg = "Create " + str(exc)[:12]
        elif kind == "Folder":
            name = self.input_bar("New folder", "folder")
            if not name: return
            try:
                os.mkdir(_join(self.folder, name)); self.msg = "Folder created"; self.refresh()
            except OSError as exc: self.msg = "Mkdir " + str(exc)[:12]

    def rename_selected(self):
        path = self.selected_path()
        if not path: return
        if len(self.marked) > 1:
            self.msg = "Rename one item"; return
        old = _basename(path); new = self.input_bar("Rename", old)
        if not new or new == old: return
        dest = _join(self.folder, new)
        if _exists(dest): self.msg = "Name exists"; return
        try:
            pyperm.require_write(path)
            os.rename(path, dest); pyperm.move(path, dest)
            if old in self.marked:
                self.marked.remove(old); self.marked.add(new)
            self.msg = "Renamed"; self.refresh()
        except OSError as exc: self.msg = "Rename " + str(exc)[:12]

    def delete_selected(self):
        targets = []
        if self.marked:
            for name in self.marked:
                for entry_name, is_dir in self.entries:
                    if entry_name == name:
                        targets.append((entry_name, is_dir)); break
        else:
            entry = self.selected_entry()
            if entry: targets.append(entry)
        if not targets: return
        label = str(len(targets)) + " selected" if len(targets) > 1 else targets[0][0][:18]
        if self.popup("Delete " + label, ("Cancel", "DELETE")) != "DELETE": return
        deleted = 0
        failed = 0
        for name, is_dir in targets:
            path = _join(self.folder, name)
            try:
                pyperm.require_write(path)
                if is_dir: os.rmdir(path)
                else: os.remove(path)
                pyperm.remove(path)
                deleted += 1
            except OSError as exc:
                print("Delete error:", name, repr(exc)); failed += 1
        self.marked.clear()
        self.msg = "Deleted " + str(deleted)
        if failed: self.msg += ", fail " + str(failed)
        self.refresh()

    def set_clipboard(self, mode):
        targets = self.selection_targets()
        if not targets:
            self.msg = "Select item"; return
        self.clipboard = targets
        self.clipboard_mode = mode
        self.marked.clear()
        self.msg = mode.capitalize() + " " + str(len(targets))

    def paste_clipboard(self):
        if not self.clipboard or not self.clipboard_mode:
            self.msg = "Clipboard empty"; return
        pasted = 0
        failed = 0
        remaining = []
        mode = self.clipboard_mode
        for src, is_dir in self.clipboard:
            if not _exists(src):
                failed += 1
                if mode == "cut": remaining.append((src, is_dir))
                continue
            dest = _join(self.folder, _basename(src))
            src_root = src.rstrip("/")
            if dest == src or _exists(dest):
                failed += 1
                if mode == "cut": remaining.append((src, is_dir))
                continue
            if is_dir and (self.folder == src_root or self.folder.startswith(src_root + "/")):
                failed += 1
                if mode == "cut": remaining.append((src, is_dir))
                continue
            try:
                if mode == "cut":
                    pyperm.require_write(src)
                    os.rename(src, dest)
                    try: pyperm.move(src, dest)
                    except Exception as exc: print("Permission move error:", repr(exc))
                elif is_dir:
                    _copy_tree(src, dest)
                else:
                    _copy_file(src, dest)
                pasted += 1
            except Exception as exc:
                print("Paste error:", _basename(src), repr(exc))
                failed += 1
                if mode == "cut": remaining.append((src, is_dir))
        if mode == "cut":
            self.clipboard = remaining
            if not remaining: self.clipboard_mode = None
        self.msg = "Pasted " + str(pasted)
        if failed: self.msg += ", fail " + str(failed)
        self.refresh()
        gc.collect()

    def clipboard_menu(self):
        mode = self.clipboard_mode.upper() if self.clipboard_mode else "EMPTY"
        title = "Clipboard " + mode
        choice = self.popup(title, (
            "Copy selected", "Cut selected", "Paste here", "Clear clipboard", "Cancel"))
        if choice == "Copy selected": self.set_clipboard("copy")
        elif choice == "Cut selected": self.set_clipboard("cut")
        elif choice == "Paste here": self.paste_clipboard()
        elif choice == "Clear clipboard":
            self.clipboard = []
            self.clipboard_mode = None
            self.msg = "Clipboard clear"

    def permission_menu(self, path=None):
        path = path or self.selected_path()
        if not path:
            self.msg = "Select item"; return
        current = pyperm.get_mode(path)
        choice = self.popup("Permissions %03o" % current, (
            "444 read only", "600 owner rw", "644 rw/r/r", "700 owner rwx",
            "755 rwx/rx/rx", "777 all rwx", "Custom", "Cancel"))
        if not choice or choice == "Cancel": return
        modes = {"444 read only":"444", "600 owner rw":"600", "644 rw/r/r":"644",
                 "700 owner rwx":"700", "755 rwx/rx/rx":"755", "777 all rwx":"777"}
        mode = modes.get(choice)
        if choice == "Custom": mode = self.input_bar("chmod mode", "%03o" % current)
        if not mode: return
        try:
            pyperm.chmod(path, mode); self.msg = "chmod " + mode
        except Exception as exc: self.msg = "chmod " + str(exc)[:12]

    def compress_selected(self, path=None):
        path = path or self.selected_path()
        if not path: self.msg = "Select item"; return
        import zipfile
        default = _basename(path.rstrip("/")) + ".zip"
        name = self.input_bar("ZIP name", default)
        if not name: return
        if not name.lower().endswith(".zip"): name += ".zip"
        archive = _join(self.folder, name)
        if _exists(archive):
            self.msg = "ZIP exists"
            return
        try:
            pyperm.require_read(path)
            zipfile.compress(path, archive); self.msg = "ZIP created"; self.refresh()
        except Exception as exc:
            print("ZIP error:", repr(exc)); self.msg = "ZIP error"

    def extract_selected(self, path=None):
        path = path or self.selected_path()
        if not path or not path.lower().endswith(".zip"): self.msg = "Select .zip"; return
        import zipfile
        default = _basename(path)[:-4] or "unzipped"
        name = self.input_bar("Extract folder", default)
        if not name: return
        try:
            pyperm.require_read(path)
            zipfile.extract(path, _join(self.folder, name)); self.msg = "ZIP extracted"; self.refresh()
        except Exception as exc:
            print("Unzip error:", repr(exc)); self.msg = "Unzip error"

    def more_menu(self):
        choice = self.popup("More", (
            "File information", "Run file", "Edit file", "Delete selected", "Clipboard", "New editor",
            "Up one folder", "Permissions", "Compress to ZIP", "Extract ZIP", "Theme",
            "PythonUltra Info", "Refresh", "Exit Files"))
        if choice == "File information":
            path = self.selected_path()
            if path and not _is_dir(path): self.file_info(path)
            else: self.msg = "Select file"
        elif choice == "Run file": self.run_file()
        elif choice == "Edit file": self.edit_file()
        elif choice == "Delete selected": self.delete_selected()
        elif choice == "Clipboard": self.clipboard_menu()
        elif choice == "New editor": self.open_editor()
        elif choice == "Up one folder":
            self.folder = _parent(self.folder); self.selected = self.scroll = 0; self.marked.clear(); self.refresh()
        elif choice == "Permissions": self.permission_menu()
        elif choice == "Compress to ZIP": self.compress_selected()
        elif choice == "Extract ZIP": self.extract_selected()
        elif choice == "Theme":
            theme = self.popup("Files Theme", self.pyeditor.THEME_NAMES)
            if theme:
                self.theme_name = theme; self.palette = self.pyeditor.THEMES[theme]; self.msg = theme
        elif choice == "PythonUltra Info":
            import pythonultra
            pythonultra.info_ui(self.theme_name not in ("GitHub Light", "PythonUltra Light"))
        elif choice == "Refresh": self.refresh()
        elif choice == "Exit Files": return "exit"
        return None

    def run(self):
        g = self.g
        while True:
            self.draw(); key = g.getkey().key
            if key == g.KEY_UP and self.entries: self.selected = max(0, self.selected - 1)
            elif key == g.KEY_DOWN and self.entries: self.selected = min(len(self.entries) - 1, self.selected + 1)
            elif key in (g.KEY_EXE, g.KEY_RIGHT): self.enter_selected()
            elif key == g.KEY_LEFT:
                self.folder = _parent(self.folder); self.selected = self.scroll = 0; self.marked.clear(); self.refresh()
            elif key == g.KEY_F1: self.toggle_selected()
            elif key == g.KEY_F2: self.sequence_menu()
            elif key == g.KEY_F3: self.search_menu()
            elif key == g.KEY_F4: self.create_new()
            elif key == g.KEY_F5: self.rename_selected()
            elif key == g.KEY_F6:
                if self.more_menu() == "exit": return
            elif key == g.KEY_OPTN:
                if self.more_menu() == "exit": return
            elif key == g.KEY_EXIT:
                if self.folder != "/":
                    self.folder = _parent(self.folder); self.selected = self.scroll = 0; self.marked.clear(); self.refresh()
                else: return


def browse(folder="/", theme="GitHub Dark"):
    return Browser(folder, theme).run()
