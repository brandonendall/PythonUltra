'''Apply the second-stage PythonUltra UI/terminal integration patches.

Runs after apply_pythonultra_features.py, so the source blocks below target the
first-stage patched shell (theme + history + NumPy fix).
'''

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.c"
CONSOLE_C = ROOT / "console.c"
CONSOLE_H = ROOT / "console.h"
BUILD_ID = ROOT / "modules" / "pythonultra" / "_build.py"


def replace_once(text, old, new, label):
    if new in text:
        return text, False
    if old not in text:
        raise SystemExit("Unable to locate PythonUltra UI2 source block: " + label)
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


def patch_console_clear():
    changed = patch(CONSOLE_H, [
        (
            '''/* Clear the current line. */
void console_clear_current_line(console_t *cons);
''',
            '''/* Clear the current line. */
void console_clear_current_line(console_t *cons);

/* Clear all terminal scrollback and create a fresh editable line. */
void console_clear(console_t *cons);
''',
            "console clear declaration",
        ),
    ])
    changed = patch(CONSOLE_C, [
        (
            '''void console_clear_current_line(console_t *cons)
{
    stredit_t *ed = last_line(cons);
    if(!ed) // avoid abort()
        return;
    stredit_delete(ed, ed->prefix, ed->size - ed->prefix);
    cons->cursor = ed->prefix;
    cons->render_needed = true;
}

//=== Terminal input ===//
''',
            '''void console_clear_current_line(console_t *cons)
{
    stredit_t *ed = last_line(cons);
    if(!ed) // avoid abort()
        return;
    stredit_delete(ed, ed->prefix, ed->size - ed->prefix);
    cons->cursor = ed->prefix;
    cons->render_needed = true;
}

void console_clear(console_t *cons)
{
    int count = cons->lines.size;
    if(count > 0)
        linebuf_recycle_oldest_lines(&cons->lines, count);
    if(cons->lines.size == 0)
        console_newline(cons);
    cons->cursor = 0;
    cons->render_needed = true;
}

//=== Terminal input ===//
''',
            "console clear implementation",
        ),
    ]) or changed
    return changed


def patch_main():
    changed = patch(MAIN, [
        (
            '''#include "py/builtin.h"
#include "py/mphal.h"
#include "py/repl.h"
''',
            '''#include "py/builtin.h"
#include "py/mphal.h"
#include "py/repl.h"
#include "py/runtime.h"
#include "py/obj.h"
#include "py/nlr.h"
''',
            "terminal runtime includes",
        ),
        (
            '''static bool pe_dark_mode = false;

const char pythonultra_help_text[] =
''',
            '''static bool pe_dark_mode = true;
static bool pe_terminal_mode = true;

const char pythonultra_help_text[] =
''',
            "default dark terminal mode",
        ),
        (
            '''    "F3: PythonUltra modules and key methods\\n";
''',
            '''    "F3: modal module/method catalog\\n"
    "F5: PythonUltra Editor   F6: Build info\\n"
    "Terminal: help, man, ls, cd, pwd, mkdir, touch, rm, mv, cat\\n"
    "Type python for REPL; exit returns to terminal\\n";
''',
            "expanded PythonUltra help",
        ),
        (
            '''static void pe_print_prompt(int which)
{
    char const *prompt = NULL;
    if(which == 2)
        prompt = mp_repl_get_ps2();
    else
        prompt = mp_repl_get_ps1();

    console_write(PE.console, prompt, -1);
    console_lock_prefix(PE.console);
}

static void pe_update_title(void)
''',
            '''static void pe_print_prompt(int which)
{
    char const *prompt = NULL;
    if(which == 2)
        prompt = mp_repl_get_ps2();
    else
        prompt = mp_repl_get_ps1();

    console_write(PE.console, prompt, -1);
    console_lock_prefix(PE.console);
}

static void pe_print_terminal_prompt(void)
{
    char cwd[128];
    char prompt[150];
    if(!getcwd(cwd, sizeof cwd))
        strcpy(cwd, "?");
    snprintf(prompt, sizeof prompt, "PU:%s$ ", cwd);
    console_write(PE.console, prompt, -1);
    console_lock_prefix(PE.console);
}

static void pe_update_title(void)
''',
            "terminal prompt",
        ),
        (
            '''static void pe_apply_theme(void)
{
    int background = pe_dark_mode ? C_BLACK : C_WHITE;
    int foreground = pe_dark_mode ? C_WHITE : C_BLACK;

    jwidget_set_background(PE.shell, background);
    widget_shell_set_text_color(PE.shell, foreground);
    PE.scene->widget.update = true;
}

static void pe_run_shell_shortcut(char const *code)
{
    pe_show_shell();
    console_clear_current_line(PE.console);
    console_newline(PE.console);
    pyexec_repl_execute(code);
    pe_print_prompt(1);
}
''',
            '''static void pe_apply_theme(void)
{
    int background = pe_dark_mode ? C_BLACK : C_WHITE;
    int foreground = pe_dark_mode ? C_WHITE : C_BLACK;

    jwidget_set_background(PE.shell, background);
    widget_shell_set_text_color(PE.shell, foreground);
    jwidget_set_background(PE.scene, background);
    jwidget_set_background(PE.title, pe_dark_mode ? C_BLACK : C_WHITE);
    jlabel_set_text_color(PE.title, pe_dark_mode ? C_WHITE : C_BLACK);
    PE.scene->widget.update = true;
}

static void pe_run_python_action(char const *code)
{
    pyexec_repl_execute(code);
    pe_apply_theme();
    PE.scene->widget.update = true;
}

static void pe_insert_catalog_selection(void)
{
    /* Preserve the edit line and cursor. A picker result is input, not code
       to execute through pyexec_repl_execute(). */
    font_t const *previous_font = dfont(NULL);
    nlr_buf_t nlr;
    if(nlr_push(&nlr) == 0) {
        mp_obj_t module = mp_import_name(MP_QSTR_pythonultra,
            mp_const_none, MP_OBJ_NEW_SMALL_INT(0));
        mp_obj_t function = mp_load_attr(module, MP_QSTR_catalog_insert_ui);
        mp_obj_t result = mp_call_function_1(function, mp_obj_new_bool(pe_dark_mode));
        if(result != mp_const_none) {
            size_t length;
            char const *text = mp_obj_str_get_data(result, &length);
            console_write_raw(PE.console, text, length);
        }
        nlr_pop();
    }
    else {
        mp_obj_print_exception(&mp_plat_print, MP_OBJ_FROM_PTR(nlr.ret_val));
    }
    dfont(previous_font);
    pe_apply_theme();
    PE.scene->widget.update = true;
}

static int pe_terminal_dispatch(char const *line)
{
    int action = 0;
    nlr_buf_t nlr;
    if(nlr_push(&nlr) == 0) {
        mp_obj_t module = mp_import_name(MP_QSTR_pyterm,
            mp_const_none, MP_OBJ_NEW_SMALL_INT(0));
        mp_obj_t function = mp_load_attr(module, MP_QSTR_dispatch);
        mp_obj_t result = mp_call_function_1(function,
            mp_obj_new_str(line, strlen(line)));
        if(mp_obj_is_int(result))
            action = mp_obj_get_int(result);
        nlr_pop();
    }
    else {
        mp_obj_print_exception(&mp_plat_print, MP_OBJ_FROM_PTR(nlr.ret_val));
    }
    return action;
}
''',
            "terminal dispatcher",
        ),
        (
            '''    if(e.type == WIDGET_SHELL_INPUT) {
        char *line = (char *)e.data;
        if(shell_bound) {
            return line;
        }
        else {
            pyexec_repl_execute(line);
            free(line);
            pe_print_prompt(1);
        }
    }
''',
            '''    if(e.type == WIDGET_SHELL_INPUT) {
        char *line = (char *)e.data;
        if(shell_bound) {
            return line;
        }
        else if(pe_terminal_mode) {
            int action = pe_terminal_dispatch(line);
            free(line);
            if(action == 1) {
                pe_terminal_mode = false;
                console_write(PE.console,
                    "PythonUltra Python REPL - type exit to return to terminal\\n", -1);
                pe_print_prompt(1);
            }
            else if(action == 2) {
                console_clear(PE.console);
                pe_print_terminal_prompt();
            }
            else if(action == 3) {
                if(exit)
                    *exit = true;
            }
            else {
                pe_print_terminal_prompt();
            }
        }
        else {
            if(!strcmp(line, "exit") || !strcmp(line, "exit()")) {
                free(line);
                pe_terminal_mode = true;
                console_write(PE.console, "Returned to PythonUltra Terminal\\n", -1);
                pe_print_terminal_prompt();
            }
            else if(!strcmp(line, "clear")) {
                free(line);
                console_clear(PE.console);
                pe_print_prompt(1);
            }
            else {
                pyexec_repl_execute(line);
                free(line);
                pe_print_prompt(1);
            }
        }
    }
''',
            "terminal/repl input modes",
        ),
        (
            '''    if(!shell_bound && show_files)
        pe_show_files();
    if(!shell_bound && show_shell)
        pe_show_shell();
    if(!shell_bound && key == KEY_F3)
        pe_run_shell_shortcut("import pythonultra as _pu; _pu.catalog()");
    if(!shell_bound && key == KEY_F4) {
        pe_dark_mode = !pe_dark_mode;
        pe_apply_theme();
    }
''',
            '''    if(!shell_bound && show_files) {
        if(pe_dark_mode)
            pe_run_python_action("import pyfiles as _pf; _pf.browse('/', 'GitHub Dark')");
        else
            pe_run_python_action("import pyfiles as _pf; _pf.browse('/', 'GitHub Light')");
        pe_show_shell();
    }
    if(!shell_bound && show_shell)
        pe_show_shell();
    if(!shell_bound && key == KEY_F3) {
        pe_insert_catalog_selection();
    }
    if(!shell_bound && key == KEY_F4) {
        pe_dark_mode = !pe_dark_mode;
        pe_apply_theme();
    }
    if(!shell_bound && key == KEY_F5) {
        if(pe_dark_mode)
            pe_run_python_action("import pyeditor as _ed; _ed.new_file('new.txt', 'GitHub Dark')");
        else
            pe_run_python_action("import pyeditor as _ed; _ed.new_file('new.txt', 'GitHub Light')");
        pe_show_shell();
    }
    if(!shell_bound && key == KEY_F6) {
        if(pe_dark_mode)
            pe_run_python_action("import pythonultra as _pu; _pu.info_ui(True)");
        else
            pe_run_python_action("import pythonultra as _pu; _pu.info_ui(False)");
    }
''',
            "enhanced F-key actions",
        ),
        (
            '''    pyexec_event_repl_init();
    pe_print_prompt(1);
''',
            '''    pyexec_event_repl_init();
    pe_print_terminal_prompt();
''',
            "initial terminal prompt",
        ),
        (
            '''    jfkeys_create2(_(&img_fkeys_main, NULL),
        "/FILES;/SHELL;/MODULES;/THEME", PE.scene);
''',
            '''    jfkeys_create2(_(&img_fkeys_main, NULL),
        "/FILES;/SHELL;/CATALOG;/THEME;/EDITOR;/INFO", PE.scene);
''',
            "six F-key labels",
        ),
        (
            '''    /* Initial state */
    jfileselect_browse(PE.fileselect, "/");
    jscene_show_and_focus(PE.scene, PE.fileselect);
''',
            '''    /* Initial state: terminal first; F1 opens enhanced Files. */
    jfileselect_browse(PE.fileselect, "/");
    jscene_show_and_focus(PE.scene, PE.shell);
    jwidget_set_visible(PE.title, PE.show_title_in_shell);
''',
            "terminal initial view",
        ),
    ])
    return changed


def write_build_id():
    try:
        build = subprocess.check_output(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=ROOT.parent.parent,
            text=True,
        ).strip()
    except Exception:
        build = "unknown"
    content = '# Generated during the PythonUltra build.\nBUILD_ID = "' + build + '"\n'
    old = BUILD_ID.read_text(encoding="utf-8") if BUILD_ID.exists() else ""
    if old != content:
        BUILD_ID.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    changed = []
    if patch_console_clear(): changed.append("clear")
    if patch_main(): changed.append("terminal-ui")
    if write_build_id(): changed.append("build-id")
    print("PythonUltra UI2: " + (", ".join(changed) if changed else "already applied"))


if __name__ == "__main__":
    main()
