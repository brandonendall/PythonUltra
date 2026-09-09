"""PythonUltra terminal command layer for the fx-CG50.

Compact Linux-like commands, persistent aliases/history/configuration and a
PythonUltra-enforced rwx permission model for calculator storage.
"""

import gc
import os
import sys
import pyperm

__version__ = "0.3.0-cg50"

ENTER_PYTHON = 1
CLEAR_SCREEN = 2
EXIT_APP = 3
FONT_SMALL = 10
FONT_NORMAL = 11
FONT_LARGE = 12
THEME_DARK = 20
THEME_LIGHT = 21
THEME_TOGGLE = 22
HISTORY_CLEAR = 30

RC_PATH = "/.pythonultrarc"
HISTORY_PATH = "/.pythonultra_history"
HISTORY_MAX_BYTES = 8192
HISTORY_KEEP_LINES = 64

_COMMANDS = (
    "help", "man", "ls", "cd", "pwd", "mkdir", "touch", "rm", "rmdir",
    "mv", "cp", "cat", "echo", "clear", "chmod", "python", "zip", "unzip",
    "edit", "files", "modules", "info", "version", "alias", "unalias",
    "source", "history", "font", "theme", "rc",
)

_MAN = {
    "help": (
        "NAME: help - list commands or show command help",
        "SYNOPSIS: help [command]",
        "EXAMPLE: help python",
        "SEE ALSO: man",
    ),
    "man": (
        "NAME: man - PythonUltra command manual",
        "SYNOPSIS: man command",
        "EXAMPLE: man chmod",
        "TIP: command -h and command --help also work",
    ),
    "ls": (
        "NAME: ls - list files and folders",
        "SYNOPSIS: ls [-l] [path]",
        "-l  show rwx permissions, byte size and name",
        "EXAMPLE: ls -l games",
    ),
    "cd": (
        "NAME: cd - change working directory",
        "SYNOPSIS: cd [path]",
        "cd .. parent; cd / storage root",
        "EXAMPLE: cd games",
    ),
    "pwd": ("NAME: pwd - print working directory", "SYNOPSIS: pwd"),
    "mkdir": (
        "NAME: mkdir - create folders",
        "SYNOPSIS: mkdir [-p] folder [folder ...]",
        "-p  create missing parent folders",
        "EXAMPLE: mkdir -p games/demo",
    ),
    "touch": (
        "NAME: touch - create a file if it does not exist",
        "SYNOPSIS: touch file [file ...]",
        "EXAMPLE: touch notes.txt",
    ),
    "rm": (
        "NAME: rm - remove files",
        "SYNOPSIS: rm file [file ...]",
        "PythonUltra write permission is required",
        "EXAMPLE: rm old.txt",
    ),
    "rmdir": (
        "NAME: rmdir - remove empty folders",
        "SYNOPSIS: rmdir folder [folder ...]",
        "EXAMPLE: rmdir old_folder",
    ),
    "mv": (
        "NAME: mv - rename or move a file/folder",
        "SYNOPSIS: mv source destination",
        "EXAMPLE: mv old.py new.py",
    ),
    "cp": (
        "NAME: cp - copy a file",
        "SYNOPSIS: cp source destination",
        "EXAMPLE: cp game.py game_backup.py",
    ),
    "cat": (
        "NAME: cat - display text file contents",
        "SYNOPSIS: cat file [file ...]",
        "PythonUltra read permission is required",
        "EXAMPLE: cat README.txt",
    ),
    "echo": (
        "NAME: echo - print text",
        "SYNOPSIS: echo [text ...]",
        "EXAMPLE: echo Hello PythonUltra",
    ),
    "clear": ("NAME: clear - clear terminal scrollback", "SYNOPSIS: clear"),
    "chmod": (
        "NAME: chmod - change PythonUltra rwx permissions",
        "SYNOPSIS: chmod MODE file [file ...]",
        "MODE uses octal read=4 write=2 execute=1",
        "EXAMPLE: chmod 444 file.txt   # read-only",
        "EXAMPLE: chmod 644 notes.txt",
        "EXAMPLE: chmod 755 hello.py   # directly executable",
        "NOTE: permissions are enforced by PythonUltra, not Casio OS",
    ),
    "python": (
        "NAME: python - enter REPL or run Python code",
        "SYNOPSIS: python",
        "          python file.py [args ...]",
        "          python -c code [args ...]",
        "          python -h | python --help | python --h | python -help",
        "python file.py follows Linux interpreter behavior: read permission",
        "Direct ./file.py additionally requires execute permission",
        "exit or exit() returns from REPL to terminal",
        "Script arguments are available through sys.argv",
        "EXAMPLE: python hello.py Brandon 42",
    ),
    "zip": (
        "NAME: zip - compress a file or folder",
        "SYNOPSIS: zip archive.zip source",
        "Uses DEFLATE compression and standard ZIP format",
        "EXAMPLE: zip project.zip project",
    ),
    "unzip": (
        "NAME: unzip - extract a ZIP archive",
        "SYNOPSIS: unzip archive.zip [destination]",
        "EXAMPLE: unzip project.zip project_copy",
    ),
    "edit": (
        "NAME: edit - open a text file in PythonUltra Editor",
        "SYNOPSIS: edit file",
        "Works with .py, .txt, .csv, .json, .md and other text",
        "EXAMPLE: edit notes.txt",
    ),
    "files": (
        "NAME: files - open graphical PythonUltra Files",
        "SYNOPSIS: files [folder]",
        "EXAMPLE: files /",
    ),
    "modules": ("NAME: modules - open PythonUltra module catalog", "SYNOPSIS: modules"),
    "info": ("NAME: info - show build/collaboration information", "SYNOPSIS: info"),
    "version": ("NAME: version - show PythonUltra/MicroPython version", "SYNOPSIS: version"),
    "alias": (
        "NAME: alias - create or list terminal aliases",
        "SYNOPSIS: alias [name=value]",
        "EXAMPLE: alias ll='ls -l'",
        "Put aliases in /.pythonultrarc to keep them after restart",
    ),
    "unalias": ("NAME: unalias - remove session alias", "SYNOPSIS: unalias name [name ...]"),
    "source": (
        "NAME: source - load shell configuration",
        "SYNOPSIS: source [file]",
        "Default file: /.pythonultrarc",
    ),
    "history": (
        "NAME: history - show persistent command history",
        "SYNOPSIS: history [-c] [count]",
        "-c  clear /.pythonultra_history",
        "UP/DOWN also keep the native current-session command history",
    ),
    "font": (
        "NAME: font - change terminal font size",
        "SYNOPSIS: font [small|normal|large]",
        "small=font_9 normal=font_13 large=font_19",
        "Persist with: set font=normal in /.pythonultrarc",
    ),
    "theme": (
        "NAME: theme - change terminal theme",
        "SYNOPSIS: theme [dark|light|toggle]",
        "Persist with: set theme=dark in /.pythonultrarc",
    ),
    "rc": (
        "NAME: rc - PythonUltra terminal configuration",
        "SYNOPSIS: rc [show|edit|reload]",
        "File: /.pythonultrarc",
    ),
}

_ALIASES = {}
DEFAULT_MENU_BORDER = 0xF800  # Red, matching PythonUltra's cybernetic-snake identity.
_SETTINGS = {"font": "normal", "theme": "dark", "startup": "files",
             "menu_border": DEFAULT_MENU_BORDER}
_STARTED = False
_RC_TEMPLATE = """# PythonUltra terminal configuration
# Read at startup. Lines beginning with # are comments.
set theme=dark
set startup=files
# Optional: color name, #RRGGBB, or 0xRGB565. Omitted -> red.
# set menu_border=red
set font=normal
# cd /games
# alias ll='ls -l'
# alias py=python
"""


def commands():
    return _COMMANDS


def man(command):
    command = str(command).strip().lower()
    pages = _MAN.get(command)
    if not pages:
        print("No manual entry for " + command)
        return False
    print("PYTHONULTRA MANUAL - " + command.upper())
    print("-" * 30)
    for line in pages:
        print(line)
    return True


def _split(line):
    result = []
    current = []
    quote = None
    escape = False
    for char in line:
        if escape:
            current.append(char)
            escape = False
        elif char == "\\":
            escape = True
        elif quote:
            if char == quote:
                quote = None
            else:
                current.append(char)
        elif char in ("'", '"'):
            quote = char
        elif char in (" ", "\t"):
            if current:
                result.append("".join(current)); current = []
        else:
            current.append(char)
    if escape:
        current.append("\\")
    if quote:
        raise ValueError("unterminated quote")
    if current:
        result.append("".join(current))
    return result


def _strip_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _exists(path):
    try:
        os.stat(path); return True
    except OSError:
        return False


def _is_dir(path):
    return pyperm.is_dir(path)


def _ensure_rc():
    if _exists(RC_PATH):
        return
    try:
        with open(RC_PATH, "w") as target:
            target.write(_RC_TEMPLATE)
    except OSError:
        pass


def _apply_rc_line(raw):
    line = raw.strip()
    if not line or line.startswith("#"):
        return
    if line.startswith("alias "):
        spec = line[6:].strip()
        if "=" in spec:
            name, value = spec.split("=", 1)
            name = name.strip(); value = _strip_quotes(value)
            if name and " " not in name:
                _ALIASES[name] = value
        return
    if line.startswith("set "):
        spec = line[4:].strip()
        if "=" not in spec:
            return
        key, value = spec.split("=", 1)
        key = key.strip().lower(); value = _strip_quotes(value).strip().lower()
        if key == "font" and value in ("small", "normal", "large"):
            _SETTINGS["font"] = value
        elif key == "theme" and value in ("dark", "light"):
            _SETTINGS["theme"] = value
        elif key == "startup" and value in ("files", "terminal"):
            _SETTINGS["startup"] = value
        elif key == "menu_border":
            color = _parse_color(value)
            if color is not None:
                _SETTINGS["menu_border"] = color
        return
    if line == "cd" or line.startswith("cd "):
        try:
            argv = _split(line)
            os.chdir(argv[1] if len(argv) > 1 else "/")
        except Exception as exc:
            print("rc cd:", exc)


def source(path=RC_PATH, reset=False):
    if reset:
        _ALIASES.clear()
        _SETTINGS["font"] = "normal"
        _SETTINGS["theme"] = "dark"
        _SETTINGS["startup"] = "files"
        _SETTINGS["menu_border"] = DEFAULT_MENU_BORDER
    try:
        with open(path, "r") as source_file:
            for line in source_file:
                _apply_rc_line(line)
        return True
    except OSError as exc:
        print("source:", path, exc)
        return False


def startup():
    """Load RC and return native config bits: font 0..2 plus dark bit 4."""
    global _STARTED
    if not _STARTED:
        _ensure_rc()
        source(RC_PATH, True)
        _STARTED = True
    font_index = {"small": 0, "normal": 1, "large": 2}.get(_SETTINGS["font"], 1)
    return font_index | (4 if _SETTINGS.get("theme") == "dark" else 0)


def startup_view():
    """Return 1 for Files and 0 for Terminal after startup RC is loaded."""
    if not _STARTED:
        startup()
    return 0 if _SETTINGS.get("startup") == "terminal" else 1


def _parse_color(value):
    names = {"cyan": 0x07FF, "red": 0xF800, "green": 0x07E0,
             "blue": 0x001F, "yellow": 0xFFE0, "magenta": 0xF81F,
             "white": 0xFFFF, "black": 0x0000, "orange": 0xFD20}
    if value in names:
        return names[value]
    try:
        if len(value) == 7 and value.startswith("#"):
            rgb = int(value[1:], 16)
            if 0 <= rgb <= 0xFFFFFF:
                return ((rgb >> 8) & 0xF800) | ((rgb >> 5) & 0x07E0) | ((rgb >> 3) & 0x001F)
        if value.startswith("0x"):
            rgb565 = int(value[2:], 16)
            if 0 <= rgb565 <= 0xFFFF:
                return rgb565
    except ValueError:
        pass
    return None


def menu_border():
    _ensure_started()
    return _SETTINGS.get("menu_border", DEFAULT_MENU_BORDER)


def _ensure_started():
    if not _STARTED:
        startup()


def _history_append(line):
    line = str(line).replace("\n", " ").strip()
    if not line:
        return
    try:
        with open(HISTORY_PATH, "a") as target:
            target.write(line + "\n")
        if os.stat(HISTORY_PATH)[6] > HISTORY_MAX_BYTES:
            with open(HISTORY_PATH, "r") as source_file:
                lines = source_file.readlines()
            with open(HISTORY_PATH, "w") as target:
                target.writelines(lines[-HISTORY_KEEP_LINES:])
    except OSError:
        pass


def _history_lines(count=None):
    try:
        with open(HISTORY_PATH, "r") as source_file:
            lines = [line.rstrip("\r\n") for line in source_file]
    except OSError:
        return []
    if count is not None:
        lines = lines[-max(0, int(count)):]
    return lines


def _expand_alias(argv):
    seen = []
    for _ in range(8):
        if not argv or argv[0] not in _ALIASES or argv[0] in seen:
            break
        seen.append(argv[0])
        argv = _split(_ALIASES[argv[0]]) + argv[1:]
    return argv


def _mkdir_p(path):
    absolute = path.startswith("/")
    current = "/" if absolute else ""
    for part in path.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            current = current.rstrip("/")
            current = current.rsplit("/", 1)[0] if "/" in current else ("/" if absolute else "")
            continue
        current = (("/" if absolute else "") + part) if current in ("", "/") else current + "/" + part
        try:
            os.mkdir(current)
        except OSError:
            if not _is_dir(current):
                raise


def _copy(src, dst):
    pyperm.require_read(src)
    if _exists(dst):
        pyperm.require_write(dst)
    with open(src, "rb") as source_file:
        with open(dst, "wb") as target:
            while True:
                block = source_file.read(1024)
                if not block:
                    break
                target.write(block)


def _run_python_file(filename, args, direct=False):
    pyperm.require_read(filename)
    if direct:
        pyperm.require_execute(filename)
    old_argv = list(sys.argv)
    old_path = list(sys.path)
    try:
        sys.argv[:] = [filename] + list(args)
        folder = filename.rsplit("/", 1)[0] if "/" in filename else os.getcwd()
        if not folder:
            folder = "/"
        if folder not in sys.path:
            sys.path.insert(0, folder)
        with open(filename, "r") as source_file:
            code = source_file.read()
        scope = {"__name__": "__main__", "__file__": filename}
        exec(code, scope, scope)
    finally:
        sys.argv[:] = old_argv
        sys.path[:] = old_path
        gc.collect()


def _run_python_code(code, args):
    old_argv = list(sys.argv)
    try:
        sys.argv[:] = ["-c"] + list(args)
        scope = {"__name__": "__main__", "__file__": "<terminal>"}
        exec(code, scope, scope)
    finally:
        sys.argv[:] = old_argv
        gc.collect()


def dispatch(line):
    _ensure_started()
    line = str(line).strip()
    if not line:
        return 0
    _history_append(line)

    try:
        argv = _expand_alias(_split(line))
    except ValueError as exc:
        print("terminal:", exc); return 0
    if not argv:
        return 0

    cmd = argv[0]
    args = argv[1:]
    lower = cmd.lower()

    # Linux-like direct executable path: chmod +x hello.py; ./hello.py arg
    if (cmd.startswith("./") or cmd.startswith("/")) and _exists(cmd) and not _is_dir(cmd):
        _run_python_file(cmd, args, True)
        return 0

    if lower not in _COMMANDS:
        print(lower + ": command not found")
        print("Type 'help' for PythonUltra commands")
        return 0

    if lower not in ("help", "man", "echo", "python") and args and args[0] in ("-h", "--help"):
        man(lower); return 0

    if lower == "help":
        if args: man(args[0])
        else:
            print("PythonUltra Terminal commands:")
            print(" ".join(_COMMANDS))
            print("Use: man COMMAND or COMMAND -h/--help")
        return 0
    if lower == "man":
        man(args[0]) if args else print("Usage: man command"); return 0
    if lower == "pwd":
        print(os.getcwd()); return 0
    if lower == "cd":
        os.chdir(args[0] if args else "/"); return 0

    if lower == "ls":
        long_form = False; path = "."
        for arg in args:
            if arg == "-l": long_form = True
            else: path = arg
        names = list(os.listdir(path)); names.sort()
        for name in names:
            full = name if path == "." else path.rstrip("/") + "/" + name
            directory = _is_dir(full)
            if long_form:
                try:
                    st = os.stat(full)
                    print("%s %8d %s" % (pyperm.format_mode(full, directory), st[6], name))
                except OSError:
                    print("??????????        ? " + name)
            else:
                print(name + ("/" if directory else ""))
        return 0

    if lower == "mkdir":
        parents = False; paths = []
        for arg in args:
            if arg == "-p": parents = True
            else: paths.append(arg)
        if not paths: print("mkdir: missing operand")
        for path in paths:
            _mkdir_p(path) if parents else os.mkdir(path)
        return 0

    if lower == "touch":
        if not args: print("touch: missing file operand")
        for path in args:
            if _exists(path): pyperm.require_write(path)
            with open(path, "ab"):
                pass
        return 0

    if lower == "chmod":
        if len(args) < 2:
            print("Usage: chmod MODE file [file ...]"); return 0
        mode = args[0]
        for path in args[1:]:
            value = pyperm.chmod(path, mode)
            print("%03o %s" % (value, pyperm.abspath(path)))
        return 0

    if lower == "rm":
        if not args: print("rm: missing file operand")
        for path in args:
            if _is_dir(path):
                print("rm: " + path + ": is a directory; use rmdir")
            else:
                pyperm.require_write(path); os.remove(path); pyperm.remove(path)
        return 0

    if lower == "rmdir":
        if not args: print("rmdir: missing directory operand")
        for path in args:
            pyperm.require_write(path); os.rmdir(path); pyperm.remove(path)
        return 0

    if lower == "mv":
        if len(args) != 2: print("Usage: mv source destination")
        else:
            pyperm.require_write(args[0]); os.rename(args[0], args[1]); pyperm.move(args[0], args[1])
        return 0

    if lower == "cp":
        _copy(args[0], args[1]) if len(args) == 2 else print("Usage: cp source destination")
        return 0

    if lower == "cat":
        if not args: print("cat: missing file operand")
        for path in args:
            pyperm.require_read(path)
            with open(path, "r") as source_file:
                while True:
                    block = source_file.read(512)
                    if not block: break
                    print(block, end="")
            print()
        return 0

    if lower == "echo":
        if args and args[0] in ("-h", "--help"): man("echo")
        else: print(" ".join(args))
        return 0
    if lower == "clear":
        return CLEAR_SCREEN

    if lower == "python":
        if not args: return ENTER_PYTHON
        if args[0] in ("-h", "--help", "--h", "-help"): man("python"); return 0
        if args[0] in ("-V", "--version"):
            print("PythonUltra MicroPython " + sys.version); return 0
        if args[0] == "-c":
            if len(args) < 2: print("python -c: missing code")
            else: _run_python_code(args[1], args[2:])
            return 0
        _run_python_file(args[0], args[1:], False); return 0

    if lower == "zip":
        if len(args) != 2: print("Usage: zip archive.zip source")
        else:
            import zipfile
            archive = args[0]
            if not archive.lower().endswith(".zip"): archive += ".zip"
            zipfile.compress(args[1], archive); print("created " + archive)
        return 0

    if lower == "unzip":
        if not args: print("Usage: unzip archive.zip [destination]")
        else:
            import zipfile
            destination = args[1] if len(args) > 1 else None
            print("extracted to " + zipfile.extract(args[0], destination))
        return 0

    if lower == "edit":
        if not args: print("Usage: edit file")
        else:
            import pyeditor
            pyeditor.open_file(args[0])
        return 0
    if lower == "files":
        import pyfiles
        pyfiles.browse(args[0] if args else os.getcwd(), "GitHub Dark" if _SETTINGS["theme"] == "dark" else "GitHub Light")
        return 0
    if lower == "modules":
        # The native shell inserts the selection after drawing the new prompt.
        return 41
    if lower == "info":
        import pythonultra
        pythonultra.info_ui(_SETTINGS["theme"] == "dark"); return 0
    if lower == "version":
        try:
            import pythonultra
            print("PythonUltra " + pythonultra.__version__ + " build " + pythonultra.BUILD_ID)
        except Exception:
            print("PythonUltra")
        print("MicroPython " + sys.version); return 0

    if lower == "alias":
        if not args:
            for name in sorted(_ALIASES):
                print("alias " + name + "='" + _ALIASES[name] + "'")
            return 0
        spec = " ".join(args)
        if "=" not in spec:
            value = _ALIASES.get(spec)
            print("alias " + spec + "='" + value + "'" if value is not None else "alias: " + spec + ": not found")
            return 0
        name, value = spec.split("=", 1); name = name.strip(); value = _strip_quotes(value)
        if not name or " " in name: print("alias: invalid name")
        else: _ALIASES[name] = value
        return 0

    if lower == "unalias":
        if not args: print("Usage: unalias name [name ...]")
        for name in args:
            if name in _ALIASES: del _ALIASES[name]
        return 0

    if lower == "source":
        source(args[0] if args else RC_PATH, False); return 0

    if lower == "history":
        if args and args[0] == "-c":
            try: os.remove(HISTORY_PATH)
            except OSError: pass
            return HISTORY_CLEAR
        count = None
        if args:
            try: count = int(args[0])
            except ValueError: print("history: count must be an integer"); return 0
        lines = _history_lines(count)
        start = max(1, len(_history_lines()) - len(lines) + 1)
        for index, item in enumerate(lines):
            print("%3d  %s" % (start + index, item))
        return 0

    if lower == "font":
        if not args:
            print(_SETTINGS["font"]); return 0
        value = args[0].lower()
        if value not in ("small", "normal", "large"):
            print("Usage: font small|normal|large"); return 0
        _SETTINGS["font"] = value
        return {"small": FONT_SMALL, "normal": FONT_NORMAL, "large": FONT_LARGE}[value]

    if lower == "theme":
        if not args:
            print(_SETTINGS["theme"]); return 0
        value = args[0].lower()
        if value == "toggle":
            _SETTINGS["theme"] = "light" if _SETTINGS["theme"] == "dark" else "dark"
            return THEME_TOGGLE
        if value not in ("dark", "light"):
            print("Usage: theme dark|light|toggle"); return 0
        _SETTINGS["theme"] = value
        return THEME_DARK if value == "dark" else THEME_LIGHT

    if lower == "rc":
        action = args[0].lower() if args else "show"
        if action == "show":
            try:
                with open(RC_PATH, "r") as source_file: print(source_file.read(), end="")
            except OSError as exc: print("rc:", exc)
        elif action == "edit":
            import pyeditor
            pyeditor.open_file(RC_PATH)
        elif action == "reload":
            source(RC_PATH, True)
            print("reloaded " + RC_PATH)
        else:
            print("Usage: rc show|edit|reload")
        return 0

    return 0
