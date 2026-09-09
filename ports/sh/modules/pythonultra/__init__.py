"""PythonUltra on-calculator reference and UI helpers."""

__version__ = "0.3.2-cg50"

try:
    from ._build import BUILD_ID
except ImportError:
    BUILD_ID = "development"

_CATALOG = (
    ("builtins", ("abs", "all", "any", "bool", "bytearray", "bytes", "chr", "compile", "dict", "dir", "enumerate", "eval", "exec", "float", "format", "getattr", "hasattr", "help", "hex", "id", "input", "int", "isinstance", "iter", "len", "list", "map", "max", "min", "next", "object", "open", "ord", "pow", "print", "range", "repr", "reversed", "round", "set", "slice", "sorted", "str", "sum", "tuple", "type", "vars", "zip")),
    ("gint", ("dclear", "dupdate", "dtext", "dline", "drect", "drect_border", "dcircle", "dellipse", "dtriangle", "getkey", "pollevent", "keydown", "image_rgb565")),
    ("numpy", ("array", "ndarray", "matrix", "mat", "asarray", "asmatrix", "zeros", "ones", "full", "identity", "eye", "arange", "linspace", "reshape", "transpose", "concatenate", "dot", "cross", "norm", "normalize", "lerp", "matmul", "sqrt", "sin", "cos", "tan", "abs", "sum", "mean", "amin", "amax")),
    ("pygame", ("Color", "Rect", "Surface", "display", "draw", "event", "key", "time", "font", "image", "transform", "sprite", "init", "quit")),
    ("py3d", ("Renderer", "cube", "vec3", "add", "sub", "scale", "dot", "cross", "length", "normalize", "identity", "matmul4", "compose", "translation", "scaling", "rotation_x", "rotation_y", "rotation_z", "transform", "focal_length", "project", "rgb565", "shade_rgb565", "prepare_triangles")),
    ("ctypes", ("c_int", "c_uint", "c_float", "c_double", "c_bool", "buffer", "read_u8", "write_u8", "fill", "copy", "available", "call")),
    ("checksum", ("sha256_file", "sha1_file")),
    ("os", ("getcwd", "chdir", "listdir", "mkdir", "remove", "unlink", "rename", "rmdir", "stat", "sep")),
    ("json", ("dumps", "loads", "dump", "load")),
    ("time", ("time", "sleep", "sleep_ms", "sleep_us", "ticks_ms", "ticks_us", "ticks_diff")),
    ("math", ("sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "atan2", "floor", "ceil", "exp", "log", "pow", "pi", "e")),
    ("random", ("random", "randint", "randrange", "choice", "getrandbits", "seed")),
    ("sys", ("path", "argv", "modules", "version", "implementation", "platform")),
    ("io", ("StringIO", "BytesIO", "FileIO")),
    ("struct", ("pack", "unpack", "calcsize")),
    ("array", ("array",)),
    ("collections", ("deque", "namedtuple", "OrderedDict")),
    ("binascii", ("crc32",)),
    ("deflate", ("DeflateIO", "RAW", "ZLIB", "GZIP", "AUTO")),
    ("zipfile", ("compress", "extract", "namelist")),
    ("pyterm", ("dispatch", "commands", "man")),
    ("pyeditor", ("Editor", "open_file", "new_file", "themes")),
    ("pyfiles", ("Browser", "browse")),
    ("casioplot", ("set_pixel", "get_pixel", "draw_string", "clear_screen", "show_screen")),
    ("kandinsky", ("color", "set_pixel", "get_pixel", "draw_string", "fill_rect")),
    ("ion", ("keydown",)),
)

UI_LIGHT = {"bg":0xFFFF, "fg":0x0000, "bar":0xD69A, "sel_bg":0x2104, "sel_fg":0xFFFF, "title":0x001F, "accent":0x07E0}
UI_DARK = {"bg":0x1082, "fg":0xD69A, "bar":0x3186, "sel_bg":0x2148, "sel_fg":0xFFFF, "title":0x7D7C, "accent":0x07FF}


def modules():
    return tuple(item[0] for item in _CATALOG)


def catalog_data(name):
    for module, methods in _CATALOG:
        if module == name:
            return methods
    return ()


def catalog(name=None):
    if name is None:
        for module, methods in _CATALOG:
            print(module + ": " + " ".join(methods))
        return None
    methods = catalog_data(str(name))
    if methods:
        print(str(name) + ": " + " ".join(methods))
        return methods
    print("Unknown catalog module: " + str(name))
    return None


def popup(title, items, dark=False):
    """Use a bounded menu font, independent of the terminal/editor size."""
    import gint
    try:
        gint.dfont_builtin("small")
        return _popup(title, items, dark)
    finally:
        gint.dfont(None)


def menu_border():
    import pyterm
    return pyterm.menu_border()


def _popup_text(gint, text, width):
    text = str(text)
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if gint.dsize(text[:middle])[0] <= width:
            low = middle
        else:
            high = middle - 1
    return text[:low]


def _popup_key(gint):
    # The native UI invokes these menus inside its key-event callback. Keep
    # the physical event transform unchanged, as in the editor's safe path.
    import time
    while True:
        event = gint.pollevent()
        if event.type == gint.KEYEV_DOWN:
            return event.key
        if event.type == gint.KEYEV_HOLD and event.key in (
                gint.KEY_UP, gint.KEY_DOWN, gint.KEY_ADD, gint.KEY_SUB):
            return event.key
        time.sleep_ms(5)


def _popup(title, items, dark=False):
    """Display a Geometry-style modal list and return the chosen item."""
    import gint
    if not items:
        return None
    colors = dict(UI_DARK if dark else UI_LIGHT)
    colors["accent"] = menu_border()
    color = colors["accent"]
    brightness = ((color >> 11) & 31) * 2 + ((color >> 5) & 63) * 3 + (color & 31)
    colors["title"] = 0x0000 if brightness >= 140 else 0xFFFF
    gint.clearevents()
    selected = 0
    scroll = 0
    max_visible = 10
    panel_x = 34
    panel_right = 362
    panel_top = 39
    row_top = 58
    row_h = 15
    title_text = str(title)
    while True:
        visible = min(len(items), max_visible)
        bottom = min(215, row_top + visible * row_h + 7)

        # Offset back layer and bright frame echo the native Geometry menus.
        gint.drect(panel_x + 5, panel_top + 5,
                   panel_right + 5, min(220, bottom + 5), colors["bar"])
        gint.drect_border(panel_x, panel_top, panel_right, bottom,
                          colors["accent"], 2, colors["bg"])

        # Active tab overlaps the frame so the modal reads like an F-key page.
        tab_x = panel_x + 14
        tab_right = min(panel_right - 12,
                        tab_x + max(94, min(214, 26 + len(title_text) * 8)))
        gint.drect_border(tab_x, panel_top - 16, tab_right, panel_top + 1,
                          colors["accent"], 2, colors["bg"])
        gint.dtext(tab_x + 8, panel_top - 13, colors["title"],
                   _popup_text(gint, title_text, tab_right - tab_x - 16))

        if selected < scroll:
            scroll = selected
        if selected >= scroll + max_visible:
            scroll = selected - max_visible + 1

        for row in range(max_visible):
            idx = scroll + row
            if idx >= len(items):
                break
            y = row_top + row * row_h
            bg = colors["sel_bg"] if idx == selected else colors["bg"]
            fg = colors["sel_fg"] if idx == selected else colors["fg"]
            gint.drect(panel_x + 8, y, panel_right - 8, y + row_h - 1, bg)
            prefix = str(row + 1) if row < 9 else "0"
            gint.dtext(panel_x + 14, y + 1, fg,
                       _popup_text(gint, prefix + ":" + str(items[idx]),
                                   panel_right - panel_x - 30))

        if scroll > 0:
            gint.dtext(panel_right - 19, panel_top + 4, colors["accent"], "^")
        if scroll + max_visible < len(items):
            gint.dtext(panel_right - 19, bottom - 12, colors["accent"], "v")

        gint.dupdate()
        key = _popup_key(gint)
        if key in (gint.KEY_EXIT, gint.KEY_LEFT):
            return None
        if key in (gint.KEY_EXE, gint.KEY_RIGHT):
            return items[selected]

        number_keys = (
            gint.KEY_1, gint.KEY_2, gint.KEY_3, gint.KEY_4, gint.KEY_5,
            gint.KEY_6, gint.KEY_7, gint.KEY_8, gint.KEY_9, gint.KEY_0,
        )
        for row, number_key in enumerate(number_keys):
            if key == number_key:
                idx = scroll + row
                if idx < len(items):
                    return items[idx]

        if key == gint.KEY_UP:
            selected = max(0, selected - 1)
        elif key == gint.KEY_DOWN:
            selected = min(len(items) - 1, selected + 1)
        elif key == gint.KEY_ADD:
            selected = min(len(items) - 1, selected + max_visible)
        elif key == gint.KEY_SUB:
            selected = max(0, selected - max_visible)


def catalog_ui(dark=False):
    """Open the F3 module -> public methods catalog."""
    while True:
        module = popup("PythonUltra Catalog", modules(), dark)
        if module is None:
            return None
        member = popup(module, catalog_data(module), dark)
        if member is not None:
            return module, member


def catalog_text(module, member):
    """Insert names, not executable examples; builtins need no module prefix."""
    return member if module == "builtins" else module + "." + member


def catalog_insert_ui(dark=False):
    selection = catalog_ui(dark)
    return catalog_text(*selection) if selection is not None else None


def information_panel(title, lines, dark=False):
    """Show read-only reference text in the established framed modal style."""
    if not dark:
        return popup(title, lines, False)

    import gint
    try:
        gint.dfont_builtin("small")
        return _information_panel(gint, title, lines)
    finally:
        gint.dfont(None)


def _information_panel(gint, title, lines):
    """Draw a dark, scrollable information panel without changing menu popups."""
    lines = tuple(str(line) for line in lines)
    if not lines:
        return None
    accent = menu_border()
    brightness = ((accent >> 11) & 31) * 2 + ((accent >> 5) & 63) * 3 + (accent & 31)
    title_color = 0x0000 if brightness >= 140 else 0xFFFF
    panel_x, panel_right = 24, 372
    panel_top, panel_bottom = 31, 211
    text_x, text_top, row_h = panel_x + 13, panel_top + 14, 15
    max_visible = (panel_bottom - text_top - 8) // row_h
    scroll = 0
    title_text = str(title)
    gint.clearevents()
    while True:
        # Keep the black body and offset frame used by the hardware-style UI.
        gint.drect(panel_x + 5, panel_top + 5, panel_right + 5, panel_bottom + 5, 0x2104)
        gint.drect_border(panel_x, panel_top, panel_right, panel_bottom, accent, 2, 0x0000)
        tab_x = panel_x + 14
        tab_right = min(panel_right - 12, tab_x + max(94, min(238, 26 + len(title_text) * 8)))
        gint.drect_border(tab_x, panel_top - 16, tab_right, panel_top + 1, accent, 2, 0x0000)
        gint.dtext(tab_x + 8, panel_top - 13, title_color,
                   _popup_text(gint, title_text, tab_right - tab_x - 16))

        for row in range(max_visible):
            index = scroll + row
            if index >= len(lines):
                break
            gint.dtext(text_x, text_top + row * row_h, 0xFFFF,
                       _popup_text(gint, lines[index], panel_right - text_x - 12))
        if scroll > 0:
            gint.dtext(panel_right - 19, panel_top + 5, accent, "^")
        if scroll + max_visible < len(lines):
            gint.dtext(panel_right - 19, panel_bottom - 14, accent, "v")

        gint.dupdate()
        key = _popup_key(gint)
        if key in (gint.KEY_EXIT, gint.KEY_LEFT, gint.KEY_RIGHT, gint.KEY_EXE):
            return None
        if key == gint.KEY_UP:
            scroll = max(0, scroll - 1)
        elif key == gint.KEY_DOWN:
            scroll = min(max(0, len(lines) - max_visible), scroll + 1)
        elif key == gint.KEY_ADD:
            scroll = min(max(0, len(lines) - max_visible), scroll + max_visible)
        elif key == gint.KEY_SUB:
            scroll = max(0, scroll - max_visible)


def info_lines():
    return (
        "PythonUltra for Casio fx-CG50",
        "Build: " + BUILD_ID,
        "MicroPython + gint + JustUI",
        "Based on PythonExtra",
        "Co-collaboration build:",
        "OffCamera-Civilman + Brandon",
        "GitHub: @brandonendall",
        "Upstream: Lephenixnoir, SlyVTT",
        "Planete Casio contributors",
        "New-display compatibility included",
        "NumPy + Pygame + py3d + Editor",
        "Files + ZIP + SHA256/SHA1",
        "Terminal + Catalog + Themes",
    )


def info_ui(dark=False):
    return information_panel("PythonUltra Info", info_lines(), dark)
