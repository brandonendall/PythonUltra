'''Add native font-size selection to PythonUltra terminal and editor.'''

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.c"
MODGINT = ROOT / "modgint.c"
EDITOR = ROOT / "modules" / "pyeditor" / "__init__.py"


def replace_once(text, old, new, label):
    if new in text:
        return text, False
    if old not in text:
        raise SystemExit("Unable to locate PythonUltra font block: " + label)
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


def patch_gint():
    return patch(MODGINT, [
        (
            '''extern void pe_enter_graphics_mode(void);\nextern void pe_dupdate(void);\n''',
            '''extern void pe_enter_graphics_mode(void);\nextern void pe_dupdate(void);\n#ifdef FXCG50\nextern font_t font_9, font_13, font_19;\n#endif\n''',
            "font resource declarations",
        ),
        (
            '''static mp_obj_t modgint_dfont(mp_obj_t new_font)\n{\n    /* This object must survive beyond the call because of course it will keep\n       getting referenced. Having only one, however, means every dfont() call\n       overrides it so we can't use the stack-style feature of getting the old\n       font back out dfont() to restore it later. */\n    static font_t font;\n    if (new_font == mp_const_none)\n        dfont(NULL);\n    else {\n        objgintfont_get(new_font, &font);\n        dfont(&font);\n    }\n\n    return mp_const_none;\n}\n''',
            '''static mp_obj_t modgint_dfont(mp_obj_t new_font)\n{\n    /* This object must survive beyond the call because of course it will keep\n       getting referenced. Having only one, however, means every dfont() call\n       overrides it so we can't use the stack-style feature of getting the old\n       font back out dfont() to restore it later. */\n    static font_t font;\n    if (new_font == mp_const_none)\n        dfont(NULL);\n    else {\n        objgintfont_get(new_font, &font);\n        dfont(&font);\n    }\n\n    return mp_const_none;\n}\n\nstatic mp_obj_t modgint_dfont_size(mp_obj_t size_obj)\n{\n#ifdef FXCG50\n    int size = mp_obj_get_int(size_obj);\n    if(size <= 9)\n        dfont(&font_9);\n    else if(size <= 13)\n        dfont(&font_13);\n    else\n        dfont(&font_19);\n#else\n    (void)size_obj;\n    dfont(NULL);\n#endif\n    return mp_const_none;\n}\n''',
            "dfont_size implementation",
        ),
        (
            '''FUN_1(dfont);\n''',
            '''FUN_1(dfont);\nFUN_1(dfont_size);\n''',
            "dfont_size function object",
        ),
        (
            '''    OBJ(dfont),\n    OBJ(dtext_opt),\n''',
            '''    OBJ(dfont),\n    OBJ(dfont_size),\n    OBJ(dtext_opt),\n''',
            "dfont_size module export",
        ),
    ])


def patch_editor():
    return patch(EDITOR, [
        (
            '''        self.theme_name = theme if theme in THEMES else DEFAULT_THEME\n        self.palette = THEMES[self.theme_name]\n        self.load_file(self.filename)\n\n    def set_theme(self, name):\n''',
            '''        self.theme_name = theme if theme in THEMES else DEFAULT_THEME\n        self.palette = THEMES[self.theme_name]\n        self.font_size = "normal"\n        self.set_font_size("normal")\n        self.load_file(self.filename)\n\n    def set_font_size(self, name):\n        global FONT_W, FONT_H, MAX_ROWS, MAX_COLS\n        presets = {\n            "small": (9, 6, 10),\n            "normal": (13, 8, 17),\n            "large": (19, 12, 23),\n        }\n        if name not in presets:\n            return False\n        pixels, width, height = presets[name]\n        self.g.dfont_size(pixels)\n        self.font_size = name\n        FONT_W = width\n        FONT_H = height\n        MAX_ROWS = max(1, (SCREEN_H - NAV_H - INFO_H) // FONT_H)\n        MAX_COLS = max(4, (SCREEN_W - TEXT_X) // FONT_W)\n        self.scroll_x = max(0, self.scroll_x)\n        self.scroll_y = max(0, self.scroll_y)\n        self.msg = "Font " + name\n        return True\n\n    def set_theme(self, name):\n''',
            "editor font state",
        ),
        (
            '''    def theme_menu(self):\n        choice = self.popup("Syntax Theme", THEME_NAMES)\n        if choice:\n            self.set_theme(choice)\n''',
            '''    def theme_menu(self):\n        action = self.popup("Editor Style", ("Syntax Theme", "Font Size", "Cancel"))\n        if action == "Syntax Theme":\n            choice = self.popup("Syntax Theme", THEME_NAMES)\n            if choice:\n                self.set_theme(choice)\n        elif action == "Font Size":\n            choice = self.popup("Font Size", ("small", "normal", "large", "Cancel"))\n            if choice and choice != "Cancel":\n                self.set_font_size(choice)\n''',
            "editor style menu",
        ),
        (
            '''        labels = ("Run", "Save", "New", "Open", "Find", "Theme")\n''',
            '''        labels = ("Run", "Save", "New", "Open", "Find", "Style")\n''',
            "editor style label",
        ),
    ])


def patch_main():
    return patch(MAIN, [
        (
            '''#else\nextern bopti_image_t const img_modifier_states;\n#define _(fx, cg) (cg)\n#endif\n''',
            '''#else\nextern bopti_image_t const img_modifier_states;\nextern font_t font_9, font_13, font_19;\n#define _(fx, cg) (cg)\n#endif\n''',
            "main font resources",
        ),
        (
            '''static int pe_terminal_dispatch(char const *line)\n{\n    int action = 0;\n''',
            '''static void pe_apply_terminal_font(int which)\n{\n#ifndef FX9860G\n    if(which <= 0)\n        widget_shell_set_font(PE.shell, &font_9);\n    else if(which == 1)\n        widget_shell_set_font(PE.shell, &font_13);\n    else\n        widget_shell_set_font(PE.shell, &font_19);\n    PE.scene->widget.update = true;\n#else\n    (void)which;\n#endif\n}\n\nstatic void pe_terminal_startup(void)\n{\n    nlr_buf_t nlr;\n    if(nlr_push(&nlr) == 0) {\n        mp_obj_t module = mp_import_name(MP_QSTR_pyterm,\n            mp_const_none, MP_OBJ_NEW_SMALL_INT(0));\n        mp_obj_t function = mp_load_attr(module, MP_QSTR_startup);\n        mp_obj_t result = mp_call_function_0(function);\n        if(mp_obj_is_int(result)) {\n            int config = mp_obj_get_int(result);\n            pe_apply_terminal_font(config & 3);\n            pe_dark_mode = (config & 4) != 0;\n            pe_apply_theme();\n        }\n        nlr_pop();\n    }\n    else {\n        mp_obj_print_exception(&mp_plat_print, MP_OBJ_FROM_PTR(nlr.ret_val));\n    }\n}\n\nstatic int pe_terminal_dispatch(char const *line)\n{\n    int action = 0;\n''',
            "terminal font/startup helpers",
        ),
        (
            '''            else if(action == 3) {\n                if(exit)\n                    *exit = true;\n            }\n            else {\n                pe_print_terminal_prompt();\n            }\n''',
            '''            else if(action == 3) {\n                if(exit)\n                    *exit = true;\n            }\n            else if(action >= 10 && action <= 12) {\n                pe_apply_terminal_font(action - 10);\n                pe_print_terminal_prompt();\n            }\n            else if(action == 20 || action == 21 || action == 22) {\n                if(action == 20) pe_dark_mode = true;\n                else if(action == 21) pe_dark_mode = false;\n                else pe_dark_mode = !pe_dark_mode;\n                pe_apply_theme();\n                pe_print_terminal_prompt();\n            }\n            else {\n                pe_print_terminal_prompt();\n            }\n''',
            "terminal action handling",
        ),
        (
            '''    /* Initial state: terminal first; F1 opens enhanced Files. */\n    jfileselect_browse(PE.fileselect, "/");\n    jscene_show_and_focus(PE.scene, PE.shell);\n    jwidget_set_visible(PE.title, PE.show_title_in_shell);\n''',
            '''    /* Initial state: terminal first; F1 opens enhanced Files. */\n    jfileselect_browse(PE.fileselect, "/");\n    jscene_show_and_focus(PE.scene, PE.shell);\n    jwidget_set_visible(PE.title, PE.show_title_in_shell);\n    pe_terminal_startup();\n''',
            "terminal startup config",
        ),
    ])


def main():
    changed = []
    if patch_gint(): changed.append("gint-fonts")
    if patch_editor(): changed.append("editor-fonts")
    if patch_main(): changed.append("terminal-fonts")
    print("PythonUltra fonts: " + (", ".join(changed) if changed else "already applied"))


if __name__ == "__main__":
    main()
