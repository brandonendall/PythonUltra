'''Patch PythonUltra Editor to respect the virtual rwx permission layer.'''

from pathlib import Path

ROOT = Path(__file__).resolve().parent
EDITOR = ROOT / "modules" / "pyeditor" / "__init__.py"


def replace_once(text, old, new, label):
    if new in text:
        return text, False
    if old not in text:
        raise SystemExit("Unable to locate permission patch block: " + label)
    return text.replace(old, new, 1), True


def main():
    text = EDITOR.read_text(encoding="utf-8")
    if "EDITOR_FIXES_VERSION = 1" in text:
        print("PythonUltra permissions: canonical editor already integrated")
        return
    changed = False

    replacements = [
        (
            '''import gc\nimport sys\n''',
            '''import gc\nimport sys\nimport pyperm\n''',
            "pyperm import",
        ),
        (
            '''    def load_file(self, filename=None):\n        if filename:\n            self.filename = filename\n        try:\n            with open(self.filename, "r") as f:\n                text = f.read()\n            self.lines = text.split("\\n") if text else [""]\n            self.msg = "Loaded"\n        except OSError:\n            self.lines = [""]\n            self.msg = "New"\n        self.cx = self.cy = self.scroll_x = self.scroll_y = 0\n        self.dirty = False\n        gc.collect()\n''',
            '''    def load_file(self, filename=None):\n        if filename:\n            self.filename = filename\n        try:\n            exists = True\n            try:\n                __import__("os").stat(self.filename)\n            except OSError:\n                exists = False\n            if exists:\n                pyperm.require_read(self.filename)\n                with open(self.filename, "r") as f:\n                    text = f.read()\n                self.lines = text.split("\\n") if text else [""]\n                self.msg = "Read only" if not pyperm.writable(self.filename) else "Loaded"\n            else:\n                self.lines = [""]\n                self.msg = "New"\n        except OSError as exc:\n            self.lines = [""]\n            self.msg = "Open " + str(exc)[:14]\n        self.cx = self.cy = self.scroll_x = self.scroll_y = 0\n        self.dirty = False\n        gc.collect()\n''',
            "editor load permissions",
        ),
        (
            '''    def save_file(self, filename=None):\n        if filename is not None:\n            self.filename = filename.strip()\n        if not self.filename:\n            self.msg = "Name error"\n            return False\n        try:\n            with open(self.filename, "w") as f:\n                f.write("\\n".join(self.lines))\n            self.dirty = False\n            self.msg = "Saved"\n            return True\n        except OSError as exc:\n            self.msg = "Save " + str(exc)[:16]\n            return False\n''',
            '''    def save_file(self, filename=None):\n        if filename is not None:\n            self.filename = filename.strip()\n        if not self.filename:\n            self.msg = "Name error"\n            return False\n        try:\n            try:\n                __import__("os").stat(self.filename)\n                pyperm.require_write(self.filename)\n            except OSError as exc:\n                if "Permission denied" in str(exc):\n                    raise\n            with open(self.filename, "w") as f:\n                f.write("\\n".join(self.lines))\n            self.dirty = False\n            self.msg = "Saved"\n            return True\n        except OSError as exc:\n            self.msg = "Save " + str(exc)[:16]\n            return False\n''',
            "editor save permissions",
        ),
        (
            '''    def run_code(self):\n        if self.dirty and not self.save_file():\n            return False\n        try:\n            with open(self.filename, "r") as f:\n                code = f.read()\n            scope = {"__name__":"__main__", "__file__":self.filename}\n            exec(code, scope, scope)\n            self.msg = "Run OK"\n        except Exception as exc:\n            print("Editor run error:", repr(exc))\n            self.msg = "Run error"\n        gc.collect()\n        return True\n''',
            '''    def run_code(self):\n        if self.dirty and not self.save_file():\n            return False\n        try:\n            pyperm.require_read(self.filename)\n            with open(self.filename, "r") as f:\n                code = f.read()\n            scope = {"__name__":"__main__", "__file__":self.filename}\n            exec(code, scope, scope)\n            self.msg = "Run OK"\n        except Exception as exc:\n            print("Editor run error:", repr(exc))\n            self.msg = "Run error"\n        gc.collect()\n        return True\n''',
            "editor run read permission",
        ),
    ]

    for old, new, label in replacements:
        text, did = replace_once(text, old, new, label)
        changed = changed or did

    if changed:
        EDITOR.write_text(text, encoding="utf-8")
    print("PythonUltra permissions: " + ("editor patched" if changed else "already applied"))


if __name__ == "__main__":
    main()
