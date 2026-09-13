"""Apply C-file execution after the existing Files/UI4 transformations."""
from pathlib import Path

path = Path(__file__).resolve().parent / "modules" / "pyfiles" / "__init__.py"
text = path.read_text(encoding="utf-8")
marker = "# PythonUltra C-file execution v1"
if marker not in text:
    changes = (
        ('action = "RUN" if lower.endswith(".py")',
         'action = "RUN" if lower.endswith((".py", ".c"))'),
        ('if lower.endswith(".py"): return self.run_file(path)',
         'if lower.endswith((".py", ".c")): return self.run_file(path)'),
        ('        return self.file_info(path)\n\n    def run_file',
         '        if path.lower().endswith(".c"):\n            return self.run_file(path)\n        return self.file_info(path)\n\n    def run_file'),
        ('not path.lower().endswith(".py"):\n            self.msg = "Run needs .py"; return',
         'not path.lower().endswith((".py", ".c")):\n            self.msg = "Run needs .py/.c"; return'),
        ('            pyperm.require_read(path)\n            folder = path.rsplit',
         '            pyperm.require_read(path)\n'
         '            if path.lower().endswith(".c"):\n'
         '                import picoc\n'
         '                result = picoc.run_file(path)\n'
         '                print("C exit code:", result)\n'
         '                self.msg = "Run OK" if result == 0 else "C error"\n'
         '                return "terminal"\n'
         '            folder = path.rsplit'),
        ('            print("File run error:", repr(exc)); self.msg = "Run error"\n',
         '            print("File run error:", repr(exc)); self.msg = "Run error"\n'
         '            return "terminal"\n'),
    )
    for old, new in changes:
        if text.count(old) != 1:
            raise SystemExit("C-file patch target not unique: " + old)
        text = text.replace(old, new, 1)
    path.write_text(text + "\n" + marker + "\n", encoding="utf-8")
print("PythonUltra C-file execution: ready")
