"""PythonUltra virtual POSIX-style permission layer.

The fx-CG50 storage filesystem does not expose POSIX chmod bits. PythonUltra
therefore keeps a tiny persistent permission table and enforces it across its
own terminal, editor, file manager and direct script launcher.
"""

import os

__version__ = "0.1.1-cg50"
DB_PATH = "/.pythonultra_permissions"
DEFAULT_FILE_MODE = 0o666
DEFAULT_DIR_MODE = 0o777

_cache = None


def abspath(path):
    path = str(path or ".")
    if not path.startswith("/"):
        base = os.getcwd()
        path = (base.rstrip("/") + "/" + path) if base != "/" else "/" + path
    parts = []
    for part in path.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            if parts:
                parts.pop()
        else:
            parts.append(part)
    return "/" + "/".join(parts)


def _load():
    global _cache
    if _cache is not None:
        return _cache
    data = {}
    try:
        with open(DB_PATH, "r") as source:
            for raw in source:
                raw = raw.rstrip("\r\n")
                if not raw or "\t" not in raw:
                    continue
                mode_text, path = raw.split("\t", 1)
                try:
                    mode = int(mode_text, 8) & 0o777
                except ValueError:
                    continue
                data[abspath(path)] = mode
    except OSError:
        pass
    _cache = data
    return data


def _save():
    data = _load()
    try:
        with open(DB_PATH, "w") as target:
            for path in sorted(data):
                target.write("%03o\t%s\n" % (data[path] & 0o777, path))
    except OSError:
        return False
    return True


def reset_cache():
    global _cache
    _cache = None


def is_dir(path):
    try:
        return bool(os.stat(path)[0] & 0x4000)
    except OSError:
        return False


def get_mode(path, directory=None):
    path = abspath(path)
    data = _load()
    if path in data:
        return data[path]
    if directory is None:
        directory = is_dir(path)
    return DEFAULT_DIR_MODE if directory else DEFAULT_FILE_MODE


def chmod(path, mode):
    path = abspath(path)
    try:
        os.stat(path)
    except OSError:
        raise OSError("No such file or directory: " + path)
    if isinstance(mode, str):
        text = mode.strip()
        if len(text) not in (3, 4) or any(ch not in "01234567" for ch in text):
            raise ValueError("mode must be octal, for example 444, 644 or 755")
        mode = int(text, 8)
    mode = int(mode) & 0o777
    _load()[path] = mode
    _save()
    return mode


def remove(path):
    path = abspath(path)
    data = _load()
    changed = False
    if path in data:
        del data[path]
        changed = True
    prefix = path.rstrip("/") + "/"
    for key in list(data):
        if key.startswith(prefix):
            del data[key]
            changed = True
    if changed:
        _save()


def move(old_path, new_path):
    old_path = abspath(old_path)
    new_path = abspath(new_path)
    data = _load()
    changed = False
    if old_path in data:
        data[new_path] = data.pop(old_path)
        changed = True
    prefix = old_path.rstrip("/") + "/"
    replacement = new_path.rstrip("/") + "/"
    for key in list(data):
        if key.startswith(prefix):
            value = data.pop(key)
            data[replacement + key[len(prefix):]] = value
            changed = True
    if changed:
        _save()


def _has(path, mask):
    return bool(get_mode(path) & mask)


def readable(path):
    return _has(path, 0o444)


def writable(path):
    return _has(path, 0o222)


def executable(path):
    return _has(path, 0o111)


def require_read(path):
    if not readable(path):
        raise OSError("Permission denied (read): " + abspath(path))
    return True


def require_write(path):
    if not writable(path):
        raise OSError("Permission denied (write): " + abspath(path))
    return True


def require_execute(path):
    if not executable(path):
        raise OSError("Permission denied (execute): " + abspath(path))
    return True


def format_mode(path, directory=None):
    mode = get_mode(path, directory)
    chars = ["d" if (directory if directory is not None else is_dir(path)) else "-"]
    for shift in (6, 3, 0):
        part = (mode >> shift) & 7
        chars.append("r" if part & 4 else "-")
        chars.append("w" if part & 2 else "-")
        chars.append("x" if part & 1 else "-")
    return "".join(chars)
