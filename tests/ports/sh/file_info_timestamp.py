"""Never render unavailable/garbage mtime fields as genuine timestamps."""
import importlib.util
from pathlib import Path
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[3]
sys.modules["pyperm"] = types.ModuleType("pyperm")
spec = importlib.util.spec_from_file_location(
    "pyfiles", ROOT / "ports/sh/modules/pyfiles/__init__.py")
files = importlib.util.module_from_spec(spec)
spec.loader.exec_module(files)
for value in (None, 0, -1, 2**56, "invalid"):
    assert files._modified_text(value) == "Unavailable"
stamp = int(time.mktime((2026, 9, 7, 11, 34, 23, 0, 0, -1)))
assert files._modified_text(stamp) == "2026-09-07 11:34:23"
sys.modules["time"] = types.ModuleType("time")
assert files._modified_text(stamp) == "Unavailable"
print("PythonUltra safe file timestamp display checks passed")
