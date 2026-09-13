'''Apply reproducible PythonUltra NumPy and shell feature patches.'''

from pathlib import Path

ROOT = Path(__file__).resolve().parent
NUMPY = ROOT / "modules" / "numpy" / "__init__.py"
MODNUMPY = ROOT / "modnumpy.c"
MPCONFIG = ROOT / "mpconfigport.h"
MAIN = ROOT / "main.c"
CONSOLE_C = ROOT / "console.c"
CONSOLE_H = ROOT / "console.h"
WIDGET_C = ROOT / "widget_shell.c"
WIDGET_H = ROOT / "widget_shell.h"


def replace_once(text, old, new, label):
    if new in text:
        return text, False
    if old not in text:
        raise SystemExit("Unable to locate PythonUltra source block: " + label)
    return text.replace(old, new, 1), True


def patch(path, replacements):
    text = path.read_text(encoding="utf-8")
    changed = False
    for old, new, label in replacements:
        text, did_change = replace_once(text, old, new, label)
        changed = changed or did_change
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def patch_numpy():
    changed = patch(MODNUMPY, [
        (
            '{ MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_numpy) },',
            '{ MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR__numpy_fast) },',
            "native numpy module name",
        ),
        (
            'MP_REGISTER_MODULE(MP_QSTR_numpy, modnumpy_module);',
            'MP_REGISTER_MODULE(MP_QSTR__numpy_fast, modnumpy_module);',
            "native numpy registration",
        ),
    ])

    changed = patch(NUMPY, [
        (
            '''import math as _math

__version__ = "0.2.0-cg50"
''',
            '''import math as _math

# Private native accelerator. Older builds registered it as "numpy", which
# shadowed this frozen package and hid numpy.matrix on the calculator.
try:
    import _numpy_fast as _fast
except ImportError:
    _fast = None

__version__ = "0.3.0-cg50"
''',
            "numpy private accelerator import",
        ),
        (
            '''def concatenate(values):
    output = []
    for value in values:
        output.extend(asarray(value).flatten()._data)
    return ndarray(output)


def dot(a, b):
''',
            '''def concatenate(values):
    output = []
    for value in values:
        output.extend(asarray(value).flatten()._data)
    return ndarray(output)


def _vector_values(value):
    if isinstance(value, ndarray):
        return list(value._data)
    return list(value)


def cross(a, b):
    left = _vector_values(a)
    right = _vector_values(b)
    if _fast is not None:
        return _fast.cross(left, right)
    if len(left) != 3 or len(right) != 3:
        raise ValueError("cross(): expected two 3D vectors")
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def norm(vector):
    values = _vector_values(vector)
    if _fast is not None:
        return _fast.norm(values)
    squared = 0
    for value in values:
        squared += value * value
    return _math.sqrt(squared)


def normalize(vector):
    values = _vector_values(vector)
    if _fast is not None:
        return _fast.normalize(values)
    magnitude = norm(values)
    if magnitude == 0:
        raise ValueError("normalize(): zero-length vector")
    return [value / magnitude for value in values]


def lerp(start, end, amount):
    left = _vector_values(start)
    right = _vector_values(end)
    if len(left) != len(right):
        raise ValueError("lerp(): vectors must have the same length")
    if _fast is not None:
        return _fast.lerp(left, right, amount)
    t = float(amount)
    return [a + (b - a) * t for a, b in zip(left, right)]


def dot(a, b):
''',
            "numpy vector compatibility helpers",
        ),
    ]) or changed
    return changed


def patch_help():
    return patch(MPCONFIG, [
        (
            '''#define MICROPY_PY_BUILTINS_HELP          (1)
#define MICROPY_PY_BUILTINS_INPUT         (1)
''',
            '''#define MICROPY_PY_BUILTINS_HELP          (1)
extern const char pythonultra_help_text[];
#define MICROPY_PY_BUILTINS_HELP_TEXT     pythonultra_help_text
#define MICROPY_PY_BUILTINS_INPUT         (1)
''',
            "PythonUltra help text configuration",
        ),
    ])


def patch_console_theme():
    changed = patch(CONSOLE_C, [
        (
            '''int console_fline_render(int x, int y, console_fline_t *FL, int w, int dy,
    int show_from, int show_until, int cursor)
''',
            '''int console_fline_render(int x, int y, console_fline_t *FL, int w, int dy,
    int show_from, int show_until, int cursor, int render_color)
''',
            "console line color argument",
        ),
        ('dline(x, y, x, y+h-1, C_BLACK);',
         'dline(x, y, x, y+h-1, render_color);',
         "empty cursor theme color"),
        ('dtext_opt(x, y, C_BLACK, C_NONE, DTEXT_LEFT, DTEXT_TOP, p, len);',
         'dtext_opt(x, y, render_color, C_NONE, DTEXT_LEFT, DTEXT_TOP, p, len);',
         "console text theme color"),
        ('dline(x+w, y, x+w, y+h-1, C_BLACK);',
         'dline(x+w, y, x+w, y+h-1, render_color);',
         "cursor theme color"),
        (
            '''void console_render(int x, int y0, console_t *cons, int dy,
    console_scrollpos_t pos)
''',
            '''void console_render(int x, int y0, console_t *cons, int dy,
    console_scrollpos_t pos, int render_color)
''',
            "console color argument",
        ),
        (
            '''        y = console_fline_render(x, y, FL, text_w, dy, -line_y,
            visible_lines - line_y, show_cursor ? cons->cursor : -1);
''',
            '''        y = console_fline_render(x, y, FL, text_w, dy, -line_y,
            visible_lines - line_y, show_cursor ? cons->cursor : -1,
            render_color);
''',
            "pass console theme color",
        ),
        (
            '''        int color = C_BLACK;
#if GINT_RENDER_RGB
        if(pos == 0) color = C_RGB(24, 24, 24);
#endif
        drect(x + text_w + scroll_spacing, y1,
              x + text_w + scroll_spacing + scroll_w - 1, y2,
              color);
''',
            '''        drect(x + text_w + scroll_spacing, y1,
              x + text_w + scroll_spacing + scroll_w - 1, y2,
              render_color);
''',
            "scrollbar theme color",
        ),
    ])
    changed = patch(CONSOLE_H, [
        (
            '''int console_fline_render(int x, int y, console_fline_t *FL, int w, int dy,
    int show_from, int show_until, int cursor);
''',
            '''int console_fline_render(int x, int y, console_fline_t *FL, int w, int dy,
    int show_from, int show_until, int cursor, int render_color);
''',
            "console line prototype",
        ),
        (
            '''void console_render(int x, int y, console_t *cons, int dy,
    console_scrollpos_t pos);
''',
            '''void console_render(int x, int y, console_t *cons, int dy,
    console_scrollpos_t pos, int render_color);
''',
            "console prototype",
        ),
    ]) or changed
    return changed


def patch_history():
    changed = patch(WIDGET_H, [
        (
            '''/* widget_shell: Multi-line Python shell input */
typedef struct {
''',
            '''/* Number of commands retained for UP/DOWN shell recall. */
#define WIDGET_SHELL_HISTORY_SIZE 16

/* widget_shell: Multi-line Python shell input */
typedef struct {
''',
            "shell history size",
        ),
        (
            '''    /* Internal information */
    int timer_id;
    uint16_t lines;
    int shift, alpha;

} widget_shell;
''',
            '''    /* Command history. history_pos == history_count means a new line. */
    char *history[WIDGET_SHELL_HISTORY_SIZE];
    int8_t history_count;
    int8_t history_pos;

    /* Internal information */
    int timer_id;
    uint16_t lines;
    int shift, alpha;

} widget_shell;
''',
            "shell history storage",
        ),
    ])

    changed = patch(WIDGET_C, [
        (
            '''#include <gint/timer.h>
#include <stdlib.h>
''',
            '''#include <gint/timer.h>
#include <stdlib.h>
#include <string.h>
''',
            "history string support",
        ),
        (
            '''    s->shift = MOD_IDLE;
    s->alpha = MOD_IDLE;

    timer_start(s->timer_id);
''',
            '''    s->shift = MOD_IDLE;
    s->alpha = MOD_IDLE;

    s->history_count = 0;
    s->history_pos = 0;
    for(int i = 0; i < WIDGET_SHELL_HISTORY_SIZE; i++)
        s->history[i] = NULL;

    timer_start(s->timer_id);
''',
            "history initialization",
        ),
        (
            '''    console_render(x, y, s->console, line_height, s->scroll);
''',
            '''    console_render(x, y, s->console, line_height, s->scroll, s->color);
''',
            "themed console rendering",
        ),
        (
            '''static void widget_shell_use_mods(widget_shell *s)
{
    int new_shift = mod_down_other(s->shift);
    int new_alpha = mod_down_other(s->alpha);

    if(new_shift != s->shift || new_alpha != s->alpha)
        jwidget_emit(s, (jevent){ .type = WIDGET_SHELL_MOD_CHANGED });

    s->shift = new_shift;
    s->alpha = new_alpha;
}

bool widget_shell_poly_event(void *s0, jevent e)
''',
            '''static void widget_shell_use_mods(widget_shell *s)
{
    int new_shift = mod_down_other(s->shift);
    int new_alpha = mod_down_other(s->alpha);

    if(new_shift != s->shift || new_alpha != s->alpha)
        jwidget_emit(s, (jevent){ .type = WIDGET_SHELL_MOD_CHANGED });

    s->shift = new_shift;
    s->alpha = new_alpha;
}

static void widget_shell_history_push(widget_shell *s, char const *line)
{
    if(!line || !line[0]) {
        s->history_pos = s->history_count;
        return;
    }

    if(s->history_count > 0 &&
       !strcmp(s->history[s->history_count - 1], line)) {
        s->history_pos = s->history_count;
        return;
    }

    char *copy = strdup(line);
    if(!copy)
        return;

    if(s->history_count == WIDGET_SHELL_HISTORY_SIZE) {
        free(s->history[0]);
        for(int i = 1; i < WIDGET_SHELL_HISTORY_SIZE; i++)
            s->history[i - 1] = s->history[i];
        s->history_count--;
    }

    s->history[s->history_count++] = copy;
    s->history_pos = s->history_count;
}

static void widget_shell_history_recall(widget_shell *s, int direction)
{
    if(s->history_count <= 0)
        return;

    if(direction < 0) {
        if(s->history_pos > 0)
            s->history_pos--;
    }
    else if(s->history_pos < s->history_count) {
        s->history_pos++;
    }

    console_clear_current_line(s->console);
    if(s->history_pos < s->history_count) {
        char const *line = s->history[s->history_pos];
        console_write_raw(s->console, line, strlen(line));
    }
    s->widget.update = true;
}

bool widget_shell_poly_event(void *s0, jevent e)
''',
            "history helpers",
        ),
        (
            '''    if(ev.key == KEY_SHIFT || ev.key == KEY_ALPHA) {
        widget_shell_update_mod(s, ev);
        return true;
    }
    if(ev.type != KEYEV_UP && ev.key == KEY_UP) {
        s->scroll++;
        s->widget.update = true;
        return true;
    }
    if(ev.type != KEYEV_UP && ev.key == KEY_DOWN) {
        s->scroll--;
        s->widget.update = true;
        return true;
    }

    if(ev.type == KEYEV_UP)
        return false;

    ev.mod = true;
    ev.shift = mod_active(s->shift);
    ev.alpha = mod_active(s->alpha);
    widget_shell_use_mods(s);

    if(ev.key == KEY_LEFT) {
''',
            '''    if(ev.key == KEY_SHIFT || ev.key == KEY_ALPHA) {
        widget_shell_update_mod(s, ev);
        return true;
    }

    if(ev.type == KEYEV_UP)
        return false;

    ev.mod = true;
    ev.shift = mod_active(s->shift);
    ev.alpha = mod_active(s->alpha);
    widget_shell_use_mods(s);

    if(ev.key == KEY_UP) {
        if(ev.shift) {
            s->scroll++;
            s->widget.update = true;
        }
        else {
            widget_shell_history_recall(s, -1);
        }
        return true;
    }
    if(ev.key == KEY_DOWN) {
        if(ev.shift) {
            s->scroll--;
            s->widget.update = true;
        }
        else {
            widget_shell_history_recall(s, +1);
        }
        return true;
    }

    if(ev.key == KEY_LEFT) {
''',
            "UP/DOWN command history",
        ),
        (
            '''    if(ev.key == KEY_EXE) {
        char *line = console_get_line(s->console, true);
        console_newline(s->console);
''',
            '''    if(ev.key == KEY_EXE) {
        char *line = console_get_line(s->console, true);
        widget_shell_history_push(s, line);
        console_newline(s->console);
''',
            "record command history",
        ),
        (
            '''void widget_shell_poly_destroy(void *s0)
{
    widget_shell *s = s0;
    timer_stop(s->timer_id);
}
''',
            '''void widget_shell_poly_destroy(void *s0)
{
    widget_shell *s = s0;
    for(int i = 0; i < s->history_count; i++)
        free(s->history[i]);
    timer_stop(s->timer_id);
}
''',
            "free command history",
        ),
    ]) or changed
    return changed


def patch_main():
    return patch(MAIN, [
        (
            '''void pe_draw(void)
{
    dclear(C_WHITE);
''',
            '''void pe_draw(void)
{
    dclear(pe_dark_mode ? C_BLACK : C_WHITE);
''',
            "theme-aware full-screen canvas",
        ),
        (
            '''struct pe_globals PE = { 0 };


//=== Hook for redirecting stdout/stderr to the shell ===//
''',
            '''struct pe_globals PE = { 0 };

static bool pe_dark_mode = false;

const char pythonultra_help_text[] =
    "PythonUltra shell help\\n"
    "F1 Files   F2 Shell   F3 Modules   F4 Theme\\n"
    "UP/DOWN: command history\\n"
    "SHIFT+UP/DOWN: scroll shell output\\n"
    "help(obj): show members of an object/module\\n"
    "help('modules'): list importable modules\\n"
    "F3: PythonUltra modules and key methods\\n";


//=== Hook for redirecting stdout/stderr to the shell ===//
''',
            "PythonUltra help text",
        ),
        (
            '''static void pe_show_shell(void)
{
    jscene_show_and_focus(PE.scene, PE.shell);
    jwidget_set_visible(PE.title, PE.show_title_in_shell);
#if GINT_HW_CP
    jbutton_set_disabled(PE.button_files, false);
    jbutton_set_disabled(PE.button_shell, true);
#endif
}

/* Handle a GUI event. If `shell_bound` is true, only actions that have an
''',
            '''static void pe_show_shell(void)
{
    jscene_show_and_focus(PE.scene, PE.shell);
    jwidget_set_visible(PE.title, PE.show_title_in_shell);
#if GINT_HW_CP
    jbutton_set_disabled(PE.button_files, false);
    jbutton_set_disabled(PE.button_shell, true);
#endif
}

static void pe_apply_theme(void)
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

/* Handle a GUI event. If `shell_bound` is true, only actions that have an
''',
            "theme and shell shortcut helpers",
        ),
        (
            '''    if(!shell_bound && show_shell)
        pe_show_shell();
    if(!shell_bound && key == KEY_VARS && e.key.shift) {
''',
            '''    if(!shell_bound && show_shell)
        pe_show_shell();
    if(!shell_bound && key == KEY_F3)
        pe_run_shell_shortcut("import pythonultra as _pu; _pu.catalog()");
    if(!shell_bound && key == KEY_F4) {
        pe_dark_mode = !pe_dark_mode;
        pe_apply_theme();
    }
    if(!shell_bound && key == KEY_VARS && e.key.shift) {
''',
            "F3 catalog and F4 theme",
        ),
        (
            '''    jfkeys_create2(_(&img_fkeys_main, NULL), "/FILES;/SHELL", PE.scene);
''',
            '''    jfkeys_create2(_(&img_fkeys_main, NULL),
        "/FILES;/SHELL;/MODULES;/THEME", PE.scene);
''',
            "F-key labels",
        ),
        (
            '''#endif

    pe_debug_get_startup_meminfo(UI);
''',
            '''#endif

    pe_apply_theme();

    pe_debug_get_startup_meminfo(UI);
''',
            "initial shell theme",
        ),
    ])


def main():
    changed = []
    for name, function in (
        ("numpy", patch_numpy),
        ("help", patch_help),
        ("console-theme", patch_console_theme),
        ("history", patch_history),
        ("shell-ui", patch_main),
    ):
        if function():
            changed.append(name)
    if changed:
        print("Applied PythonUltra feature patches: " + ", ".join(changed))
    else:
        print("PythonUltra feature patches already applied")


if __name__ == "__main__":
    main()
