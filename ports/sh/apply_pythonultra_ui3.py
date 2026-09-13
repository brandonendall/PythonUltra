'''Final PythonUltra terminal/editor integration stage.

Runs after the original feature/UI/permission patches. It connects persistent
terminal configuration to the native shell, adds real calculator font choices
(including build-generated JetBrains Mono), and removes reliance on libc
getcwd/chdir by using PythonUltra's path layer.
'''

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.c"
WIDGET_C = ROOT / "widget_shell.c"
WIDGET_H = ROOT / "widget_shell.h"
MODGINT = ROOT / "modgint.c"
PYTERM = ROOT / "modules" / "pyterm" / "__init__.py"
EDITOR = ROOT / "modules" / "pyeditor" / "__init__.py"


def replace_once(text, old, new, label):
    if new in text:
        return text, False
    if old not in text:
        raise SystemExit("Unable to locate PythonUltra UI3 block: " + label)
    return text.replace(old, new, 1), True


def patch(path, replacements):
    text = path.read_text(encoding="utf-8")
    changed = False
    for old, new, label in replacements:
        text, did = replace_once(text, old, new, label)
        changed = changed or did
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def patch_history_api():
    changed = patch(WIDGET_H, [
        (
            '''void widget_shell_set_line_spacing(widget_shell *shell, int line_spacing);\n''',
            '''void widget_shell_set_line_spacing(widget_shell *shell, int line_spacing);\n\n/* Persistent-history bridge used by PythonUltra terminal startup. */\nvoid widget_shell_history_add(widget_shell *shell, char const *line);\nvoid widget_shell_history_clear(widget_shell *shell);\n''',
            "history bridge declarations",
        ),
    ])
    changed = patch(WIDGET_C, [
        (
            '''static void widget_shell_history_recall(widget_shell *s, int direction)\n{\n''',
            '''void widget_shell_history_add(widget_shell *s, char const *line)\n{\n    widget_shell_history_push(s, line);\n}\n\nvoid widget_shell_history_clear(widget_shell *s)\n{\n    for(int i = 0; i < s->history_count; i++) {\n        free(s->history[i]);\n        s->history[i] = NULL;\n    }\n    s->history_count = 0;\n    s->history_pos = 0;\n}\n\nstatic void widget_shell_history_recall(widget_shell *s, int direction)\n{\n''',
            "history bridge implementation",
        ),
    ]) or changed
    return changed


def patch_builtin_fonts():
    changed = patch(MODGINT, [
        (
            '''// TODO: modgint: Font management?\n\nstatic mp_obj_t modgint_dtext_opt''',
            '''// PythonUltra embedded font selector. The JetBrains Mono raster fonts are\n// generated from the official OFL source at build time and converted by fxconv.\n#if defined(FXCG50)\nextern font_t font_9, font_13, font_19;\nextern font_t font_jb_9, font_jb_13, font_jb_19;\n\nstatic mp_obj_t modgint_dfont_builtin(mp_obj_t name_in)\n{\n    char const *name = mp_obj_str_get_str(name_in);\n    font_t *font = NULL;\n    int width = 0, height = 0;\n    if(!strcmp(name, "small")) { font=&font_9; width=9; height=10; }\n    else if(!strcmp(name, "normal")) { font=&font_13; width=12; height=17; }\n    else if(!strcmp(name, "large")) { font=&font_19; width=18; height=23; }\n    else if(!strcmp(name, "jetbrains-small") || !strcmp(name, "jb-small")) { font=&font_jb_9; width=9; height=10; }\n    else if(!strcmp(name, "jetbrains-normal") || !strcmp(name, "jetbrains") || !strcmp(name, "jb-normal")) { font=&font_jb_13; width=12; height=17; }\n    else if(!strcmp(name, "jetbrains-large") || !strcmp(name, "jb-large")) { font=&font_jb_19; width=18; height=23; }\n    else mp_raise_ValueError("unknown built-in font");\n    dfont(font);\n    mp_obj_t items[2] = { MP_OBJ_NEW_SMALL_INT(width), MP_OBJ_NEW_SMALL_INT(height) };\n    return mp_obj_new_tuple(2, items);\n}\nMP_DEFINE_CONST_FUN_OBJ_1(modgint_dfont_builtin_obj, modgint_dfont_builtin);\n#endif\n\nstatic mp_obj_t modgint_dtext_opt''',
            "built-in font selector",
        ),
        (
            '''    OBJ(dfont),\n    OBJ(dsize),\n    OBJ(dtext_opt),\n''',
            '''    OBJ(dfont),\n#if defined(FXCG50)\n    OBJ(dfont_builtin),\n#endif\n    OBJ(dsize),\n    OBJ(dtext_opt),\n''',
            "font selector export",
        ),
    ])
    return changed


def patch_terminal_python():
    changed = patch(PYTERM, [
        (
            '''FONT_SMALL = 10\nFONT_NORMAL = 11\nFONT_LARGE = 12\nTHEME_DARK = 20\n''',
            '''FONT_SMALL = 10\nFONT_NORMAL = 11\nFONT_LARGE = 12\nFONT_JB_SMALL = 13\nFONT_JB_NORMAL = 14\nFONT_JB_LARGE = 15\nTHEME_DARK = 20\n''',
            "JetBrains terminal action codes",
        ),
        (
            '''HISTORY_CLEAR = 30\n''',
            '''HISTORY_CLEAR = 30\nRELOAD_CONFIG = 40\n''',
            "terminal reload action",
        ),
        (
            '''        "NAME: font - change terminal font size",\n        "SYNOPSIS: font [small|normal|large]",\n        "small=font_9 normal=font_13 large=font_19",\n        "Persist with: set font=normal in /.pythonultrarc",\n''',
            '''        "NAME: font - change terminal font family/size",\n        "SYNOPSIS: font small|normal|large",\n        "          font jetbrains-small|jetbrains-normal|jetbrains-large",\n        "EXAMPLE: font jetbrains-small",\n        "Persist with: set font=jetbrains-small in /.pythonultrarc",\n''',
            "font manual",
        ),
        (
            '''set font=normal\n# cd /games\n''',
            '''set font=normal\n# Other font choices: small, large, jetbrains-small, jetbrains-normal, jetbrains-large\n# cd /games\n''',
            "rc font examples",
        ),
        (
            '''        if key == "font" and value in ("small", "normal", "large"):\n            _SETTINGS["font"] = value\n''',
            '''        if key == "font" and value in ("small", "normal", "large", "jetbrains-small", "jetbrains-normal", "jetbrains-large"):\n            _SETTINGS["font"] = value\n''',
            "rc JetBrains font parsing",
        ),
        (
            '''def startup():\n    """Load RC and return native config bits: font 0..2 plus dark bit 4."""\n    global _STARTED\n    if not _STARTED:\n        _ensure_rc()\n        source(RC_PATH, True)\n        _STARTED = True\n    font_index = {"small": 0, "normal": 1, "large": 2}.get(_SETTINGS["font"], 1)\n    return font_index | (4 if _SETTINGS.get("theme") == "dark" else 0)\n''',
            '''def _font_action(value):\n    return {\n        "small": FONT_SMALL, "normal": FONT_NORMAL, "large": FONT_LARGE,\n        "jetbrains-small": FONT_JB_SMALL,\n        "jetbrains-normal": FONT_JB_NORMAL,\n        "jetbrains-large": FONT_JB_LARGE,\n    }.get(value, FONT_NORMAL)\n\n\ndef config():\n    """Return native config: font action + 100 when dark mode is selected."""\n    return _font_action(_SETTINGS.get("font", "normal")) + (100 if _SETTINGS.get("theme") == "dark" else 0)\n\n\ndef startup():\n    """Load /.pythonultrarc and return the encoded native terminal config."""\n    global _STARTED\n    if not _STARTED:\n        _ensure_rc()\n        source(RC_PATH, True)\n        _STARTED = True\n    return config()\n\n\ndef history_tail():\n    """Return commands restored into the native UP/DOWN recall buffer."""\n    return tuple(_history_lines(16))\n''',
            "startup config and persistent history bridge",
        ),
        (
            '''    if lower == "source":\n        source(args[0] if args else RC_PATH, False); return 0\n''',
            '''    if lower == "source":\n        source(args[0] if args else RC_PATH, False); return RELOAD_CONFIG\n''',
            "source reload native config",
        ),
        (
            '''        if value not in ("small", "normal", "large"):\n            print("Usage: font small|normal|large"); return 0\n        _SETTINGS["font"] = value\n        return {"small": FONT_SMALL, "normal": FONT_NORMAL, "large": FONT_LARGE}[value]\n''',
            '''        if value not in ("small", "normal", "large", "jetbrains-small", "jetbrains-normal", "jetbrains-large"):\n            print("Usage: font small|normal|large|jetbrains-small|jetbrains-normal|jetbrains-large"); return 0\n        _SETTINGS["font"] = value\n        return _font_action(value)\n''',
            "font command JetBrains choices",
        ),
        (
            '''        elif action == "reload":\n            source(RC_PATH, True)\n            print("reloaded " + RC_PATH)\n        else:\n            print("Usage: rc show|edit|reload")\n        return 0\n''',
            '''        elif action == "reload":\n            source(RC_PATH, True)\n            print("reloaded " + RC_PATH)\n            return RELOAD_CONFIG\n        else:\n            print("Usage: rc show|edit|reload")\n        return 0\n''',
            "rc reload native config",
        ),
    ])
    return changed


def patch_editor():
    if "EDITOR_FIXES_VERSION = 1" in EDITOR.read_text(encoding="utf-8"):
        return False
    changed = patch(EDITOR, [
        (
            '''FONT_W = 8\nFONT_H = 11\nTEXT_X = 2\nMAX_ROWS = (SCREEN_H - NAV_H - INFO_H) // FONT_H\nMAX_COLS = (SCREEN_W - TEXT_X) // FONT_W\n''',
            '''FONT_W = 9\nFONT_H = 10\nTEXT_X = 2\nMAX_ROWS = (SCREEN_H - NAV_H - INFO_H) // FONT_H\nMAX_COLS = (SCREEN_W - TEXT_X) // FONT_W\n\nFONT_OPTIONS = (\n    "JetBrains Small", "JetBrains Normal", "JetBrains Large",\n    "System Small", "System Normal", "System Large",\n)\nFONT_CONFIG = {\n    "JetBrains Small": ("jetbrains-small", 9, 10),\n    "JetBrains Normal": ("jetbrains-normal", 12, 17),\n    "JetBrains Large": ("jetbrains-large", 18, 23),\n    "System Small": ("small", 9, 10),\n    "System Normal": ("normal", 12, 17),\n    "System Large": ("large", 18, 23),\n}\nDEFAULT_FONT = "JetBrains Small"\n''',
            "editor dynamic font metrics",
        ),
        (
            '''        self.palette = THEMES[self.theme_name]\n        self.load_file(self.filename)\n''',
            '''        self.palette = THEMES[self.theme_name]\n        self.font_name = DEFAULT_FONT\n        self.apply_font(self.font_name)\n        self.load_file(self.filename)\n''',
            "editor default JetBrains font",
        ),
        (
            '''    def set_theme(self, name):\n        if name in THEMES:\n            self.theme_name = name\n            self.palette = THEMES[name]\n            self.msg = name\n\n    def resolve_char''',
            '''    def set_theme(self, name):\n        if name in THEMES:\n            self.theme_name = name\n            self.palette = THEMES[name]\n            self.msg = name\n\n    def apply_font(self, name):\n        global FONT_W, FONT_H, MAX_ROWS, MAX_COLS\n        if name not in FONT_CONFIG:\n            return False\n        builtin, width, height = FONT_CONFIG[name]\n        self.g.dfont_builtin(builtin)\n        FONT_W, FONT_H = width, height\n        MAX_ROWS = max(1, (SCREEN_H - NAV_H - INFO_H) // FONT_H)\n        MAX_COLS = max(4, (SCREEN_W - TEXT_X) // FONT_W)\n        self.font_name = name\n        self.scroll_x = self.scroll_y = 0\n        self.msg = name\n        return True\n\n    def resolve_char''',
            "editor font application",
        ),
        (
            '''    def popup(self, title, items):\n        import pythonultra\n        dark = self.theme_name != "GitHub Light" and self.theme_name != "PythonUltra Light"\n        return pythonultra.popup(title, tuple(items), dark)\n''',
            '''    def popup(self, title, items):\n        import pythonultra\n        dark = self.theme_name != "GitHub Light" and self.theme_name != "PythonUltra Light"\n        result = pythonultra.popup(title, tuple(items), dark)\n        self.apply_font(self.font_name)\n        return result\n''',
            "restore editor font after popup",
        ),
        (
            '''    def theme_menu(self):\n        choice = self.popup("Syntax Theme", THEME_NAMES)\n        if choice:\n            self.set_theme(choice)\n\n    def catalog_menu''',
            '''    def style_menu(self):\n        action = self.popup("Editor Style", ("Syntax Theme", "Font / Size", "Cancel"))\n        if action == "Syntax Theme":\n            choice = self.popup("Syntax Theme", THEME_NAMES)\n            if choice:\n                self.set_theme(choice)\n        elif action == "Font / Size":\n            choice = self.popup("Editor Font", FONT_OPTIONS)\n            if choice:\n                self.apply_font(choice)\n\n    def catalog_menu''',
            "editor combined style menu",
        ),
        (
            '''            if k == g.KEY_F6:\n                self.theme_menu(); continue\n''',
            '''            if k == g.KEY_F6:\n                self.style_menu(); continue\n''',
            "editor F6 style menu",
        ),
        (
            '''    def run_code(self):\n        if self.dirty and not self.save_file():\n            return False\n''',
            '''    def run_code(self):\n        if not self.filename.lower().endswith(".py"):\n            self.msg = "Run needs .py"\n            return False\n        if self.dirty and not self.save_file():\n            return False\n''',
            "editor run Python files only",
        ),
        (
            '''            if k == g.KEY_EXIT:\n                if self.confirm_discard(): return "exit"\n''',
            '''            if k == g.KEY_EXIT:\n                if self.confirm_discard():\n                    g.dfont(None)\n                    return "exit"\n''',
            "restore default font on editor exit",
        ),
    ])
    return changed


def patch_main_native():
    return patch(MAIN, [
        (
            '''#include "resources.h"\n''',
            '''#include "resources.h"\n#include "pathutil.h"\n''',
            "pathutil include",
        ),
        (
            '''static bool pe_dark_mode = true;\nstatic bool pe_terminal_mode = true;\n\nconst char pythonultra_help_text[] =\n''',
            '''static bool pe_dark_mode = true;\nstatic bool pe_terminal_mode = true;\n\n#if defined(FXCG50)\nextern font_t font_9, font_13, font_19;\nextern font_t font_jb_9, font_jb_13, font_jb_19;\n#endif\n\nconst char pythonultra_help_text[] =\n''',
            "terminal font symbols",
        ),
        (
            '''static void pe_print_terminal_prompt(void)\n{\n    char cwd[128];\n    char prompt[150];\n    if(!getcwd(cwd, sizeof cwd))\n        strcpy(cwd, "?");\n    snprintf(prompt, sizeof prompt, "PU:%s$ ", cwd);\n    console_write(PE.console, prompt, -1);\n    console_lock_prefix(PE.console);\n}\n''',
            '''static void pe_print_terminal_prompt(void)\n{\n    char prompt[PE_PATH_MAX + 8];\n    snprintf(prompt, sizeof prompt, "PU:%s$ ", pe_path_getcwd());\n    console_write(PE.console, prompt, -1);\n    console_lock_prefix(PE.console);\n}\n''',
            "terminal prompt virtual cwd",
        ),
        (
            '''static int pe_terminal_dispatch(char const *line)\n{\n    int action = 0;\n''',
            '''static void pe_apply_terminal_font(int action)\n{\n#if defined(FXCG50)\n    font_t const *font = NULL;\n    if(action == 10) font = &font_9;\n    else if(action == 11) font = &font_13;\n    else if(action == 12) font = &font_19;\n    else if(action == 13) font = &font_jb_9;\n    else if(action == 14) font = &font_jb_13;\n    else if(action == 15) font = &font_jb_19;\n    if(font) {\n        widget_shell_set_font(PE.shell, font);\n        PE.scene->widget.update = true;\n    }\n#else\n    (void)action;\n#endif\n}\n\nstatic int pe_terminal_dispatch(char const *line)\n{\n    int action = 0;\n''',
            "native terminal font application",
        ),
        (
            '''    return action;\n}\n\n/* Handle a GUI event.''',
            '''    return action;\n}\n\nstatic int pe_pyterm_call_int0(qstr attr)\n{\n    int result = 0;\n    nlr_buf_t nlr;\n    if(nlr_push(&nlr) == 0) {\n        mp_obj_t module = mp_import_name(MP_QSTR_pyterm, mp_const_none, MP_OBJ_NEW_SMALL_INT(0));\n        mp_obj_t function = mp_load_attr(module, attr);\n        mp_obj_t value = mp_call_function_0(function);\n        if(mp_obj_is_int(value)) result = mp_obj_get_int(value);\n        nlr_pop();\n    }\n    else mp_obj_print_exception(&mp_plat_print, MP_OBJ_FROM_PTR(nlr.ret_val));\n    return result;\n}\n\nstatic void pe_terminal_apply_config(void)\n{\n    int config = pe_pyterm_call_int0(MP_QSTR_config);\n    pe_dark_mode = config >= 100;\n    if(pe_dark_mode) config -= 100;\n    pe_apply_terminal_font(config);\n    pe_apply_theme();\n}\n\nstatic void pe_terminal_load_startup(void)\n{\n    int config = pe_pyterm_call_int0(MP_QSTR_startup);\n    pe_dark_mode = config >= 100;\n    if(pe_dark_mode) config -= 100;\n    pe_apply_terminal_font(config);\n    pe_apply_theme();\n\n    nlr_buf_t nlr;\n    if(nlr_push(&nlr) == 0) {\n        mp_obj_t module = mp_import_name(MP_QSTR_pyterm, mp_const_none, MP_OBJ_NEW_SMALL_INT(0));\n        mp_obj_t function = mp_load_attr(module, MP_QSTR_history_tail);\n        mp_obj_t history = mp_call_function_0(function);\n        size_t count = 0; mp_obj_t *items = NULL;\n        mp_obj_get_array(history, &count, &items);\n        widget_shell_history_clear(PE.shell);\n        for(size_t i = 0; i < count; i++)\n            widget_shell_history_add(PE.shell, mp_obj_str_get_str(items[i]));\n        nlr_pop();\n    }\n    else mp_obj_print_exception(&mp_plat_print, MP_OBJ_FROM_PTR(nlr.ret_val));\n}\n\n/* Handle a GUI event.''',
            "terminal startup config bridge",
        ),
        (
            '''            else if(action == 3) {\n                if(exit)\n                    *exit = true;\n            }\n            else {\n                pe_print_terminal_prompt();\n            }\n''',
            '''            else if(action == 3) {\n                if(exit) *exit = true;\n            }\n            else {\n                if(action >= 10 && action <= 15) pe_apply_terminal_font(action);\n                else if(action == 20) { pe_dark_mode = true; pe_apply_theme(); }\n                else if(action == 21) { pe_dark_mode = false; pe_apply_theme(); }\n                else if(action == 22) { pe_dark_mode = !pe_dark_mode; pe_apply_theme(); }\n                else if(action == 30) widget_shell_history_clear(PE.shell);\n                else if(action == 40) pe_terminal_apply_config();\n                pe_print_terminal_prompt();\n            }\n''',
            "terminal action codes",
        ),
        (
            '''    /* Initial state: terminal first; F1 opens enhanced Files. */\n    jfileselect_browse(PE.fileselect, "/");\n    jscene_show_and_focus(PE.scene, PE.shell);\n    jwidget_set_visible(PE.title, PE.show_title_in_shell);\n''',
            '''    /* Initial state: terminal first; restore RC, theme, font and history. */\n    jfileselect_browse(PE.fileselect, "/");\n    jscene_show_and_focus(PE.scene, PE.shell);\n    jwidget_set_visible(PE.title, PE.show_title_in_shell);\n    pe_terminal_load_startup();\n    console_clear(PE.console);\n    pe_print_terminal_prompt();\n''',
            "terminal startup restoration",
        ),
        (
            '''mp_import_stat_t mp_import_stat(const char *path)\n{\n    struct stat st;\n    int rc = stat(path, &st);\n''',
            '''mp_import_stat_t mp_import_stat(const char *path)\n{\n    struct stat st;\n    char resolved[PE_PATH_MAX];\n    if(pe_path_resolve(path, resolved, sizeof resolved) < 0)\n        return MP_IMPORT_STAT_NO_EXIST;\n    int rc = stat(resolved, &st);\n''',
            "imports use virtual cwd",
        ),
    ])


def main():
    changed = []
    if patch_history_api(): changed.append("history")
    if patch_builtin_fonts(): changed.append("gint-fonts")
    if patch_terminal_python(): changed.append("terminal")
    if patch_editor(): changed.append("editor-fonts")
    if patch_main_native(): changed.append("native-ui")
    print("PythonUltra UI3: " + (", ".join(changed) if changed else "already applied"))


if __name__ == "__main__":
    main()
