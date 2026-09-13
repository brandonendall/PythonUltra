'''Add PythonUltra's SHIFT+DEL programming-symbol picker to the native shell.'''

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.c"
WIDGET_C = ROOT / "widget_shell.c"
WIDGET_H = ROOT / "widget_shell.h"
PYULTRA = ROOT / "modules" / "pythonultra" / "__init__.py"
PYTERM = ROOT / "modules" / "pyterm" / "__init__.py"


def replace_once(text, old, new, label):
    if new in text:
        return text, False
    if old not in text:
        raise SystemExit("Unable to locate PythonUltra symbol block: " + label)
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


def patch_python_ui():
    return patch(PYULTRA, [
        (
            '''\n\ndef modules():\n''',
            '''\n\n# Common ASCII characters used in Python, shell commands, paths, expressions,\n# data formats and general programming. Build them at runtime because frozen\n# punctuation QSTRs can surface as names such as _hyphen_ on calculator hardware.\n_PROGRAMMING_SYMBOL_CODES = (\n    64, 35, 36, 37, 94, 38, 42, 33, 63, 126, 96,\n    60, 62, 61, 43, 45, 47, 92, 124, 95,\n    40, 41, 91, 93, 123, 125, 39, 34, 58, 59, 44, 46,\n)\n_PROGRAMMING_SYMBOLS = tuple(chr(code) for code in _PROGRAMMING_SYMBOL_CODES)\n\n\ndef modules():\n''',
            "programming symbol list",
        ),
        (
            '''def catalog_ui(dark=False):\n''',
            '''def symbol_ui(dark=False):\n    """Open the SHIFT+DEL programming-symbol picker and return one character."""\n    return popup("Programming Symbols", _PROGRAMMING_SYMBOLS, dark)\n\n\ndef catalog_ui(dark=False):\n''',
            "symbol UI helper",
        ),
    ])


def patch_terminal_help():
    # On hardware a frozen '-' QSTR can render as the internal name _hyphen_.
    # Construct the manual rule from ASCII 45 at runtime instead.
    return patch(PYTERM, [
        (
            '''    print("-" * 30)\n''',
            '''    print(chr(45) * 30)\n''',
            "terminal manual separator",
        ),
    ])


def patch_widget():
    changed = patch(WIDGET_H, [
        (
            '''extern uint16_t WIDGET_SHELL_MOD_CHANGED;\nextern uint16_t WIDGET_SHELL_INPUT;\n''',
            '''extern uint16_t WIDGET_SHELL_MOD_CHANGED;\nextern uint16_t WIDGET_SHELL_INPUT;\nextern uint16_t WIDGET_SHELL_SYMBOLS;\n''',
            "symbol event declaration",
        ),
    ])
    changed = patch(WIDGET_C, [
        (
            '''J_DEFINE_EVENTS(WIDGET_SHELL_MOD_CHANGED, WIDGET_SHELL_INPUT)\n''',
            '''J_DEFINE_EVENTS(WIDGET_SHELL_MOD_CHANGED, WIDGET_SHELL_INPUT, WIDGET_SHELL_SYMBOLS)\n''',
            "symbol event definition",
        ),
        (
            '''    if(ev.key == KEY_DEL) {\n        console_delete_at_cursor(s->console, 1);\n        return true;\n    }\n''',
            '''    if(ev.key == KEY_DEL) {\n        if(ev.shift)\n            jwidget_emit(s, (jevent){ .type = WIDGET_SHELL_SYMBOLS });\n        else\n            console_delete_at_cursor(s->console, 1);\n        return true;\n    }\n''',
            "SHIFT+DEL symbol event",
        ),
    ]) or changed
    return changed


def patch_main():
    return patch(MAIN, [
        (
            '''    if(e.type == WIDGET_SHELL_MOD_CHANGED)\n        PE.scene->widget.update = true;\n\n    if(e.type == WIDGET_SHELL_INPUT) {\n''',
            '''    if(e.type == WIDGET_SHELL_MOD_CHANGED)\n        PE.scene->widget.update = true;\n\n    if(e.type == WIDGET_SHELL_SYMBOLS) {\n        nlr_buf_t nlr;\n        if(nlr_push(&nlr) == 0) {\n            mp_obj_t module = mp_import_name(MP_QSTR_pythonultra,\n                mp_const_none, MP_OBJ_NEW_SMALL_INT(0));\n            mp_obj_t function = mp_load_attr(module, MP_QSTR_symbol_ui);\n            mp_obj_t args[1] = { mp_obj_new_bool(pe_dark_mode) };\n            mp_obj_t result = mp_call_function_n_kw(function, 1, 0, args);\n            if(result != mp_const_none) {\n                char const *symbol = mp_obj_str_get_str(result);\n                console_write_raw(PE.console, symbol, strlen(symbol));\n                PE.scene->widget.update = true;\n            }\n            nlr_pop();\n        }\n        else {\n            mp_obj_print_exception(&mp_plat_print, MP_OBJ_FROM_PTR(nlr.ret_val));\n        }\n    }\n\n    if(e.type == WIDGET_SHELL_INPUT) {\n''',
            "terminal symbol picker handler",
        ),
    ])


def main():
    changed = []
    if patch_python_ui(): changed.append("catalog")
    if patch_terminal_help(): changed.append("manual")
    if patch_widget(): changed.append("widget")
    if patch_main(): changed.append("native")
    print("PythonUltra symbols: " + (", ".join(changed) if changed else "already applied"))


if __name__ == "__main__":
    main()
