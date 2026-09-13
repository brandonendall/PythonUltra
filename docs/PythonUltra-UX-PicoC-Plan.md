# PythonUltra UX and PicoC Integration Plan

This document records the calculator behaviors and design targets confirmed from hardware screenshots and the current PythonUltra direction.

## Editor catalog behavior

PythonUltra should preserve the calculator-friendly catalog workflow shown on hardware:

- `SHIFT + 4` opens `Catalog` from the editor.
- The first level lists supported Python modules such as `builtins`, `gint`, `numpy`, `pygame`, `time`, `math`, `random`, `sys`, `io`, `struct`, and `array`.
- Selecting a module opens a second list containing that module's available members.
- Selecting a member inserts the correct spelling into the editor at the cursor.
- Punctuation in inserted names must remain literal on hardware. In particular, member insertion must produce forms such as `pygame.image` or `py3d.cube`, never QSTR-safe spellings such as `pygame__dot__image`.
- `EXIT` from a member list backs out to the module list. `EXIT` again returns to the editor rather than quitting the editor immediately.
- This flow should remain regression-tested because it is a high-value calculator editing feature.

## Unsaved-changes exit behavior

The editor must protect unsaved work.

When the buffer is dirty and the user attempts to quit, show an `Unsaved Changes!` confirmation with the same simple hierarchy demonstrated on hardware:

1. `Cancel` — return to the editor and keep all unsaved changes.
2. `Ignore & Proceed` — leave the editor without saving.

When the buffer is already clean, normal exit does not need this warning.

The intended navigation hierarchy is therefore:

`member list -> module list -> editor -> unsaved-changes confirmation -> exit`

## PyEditorRC-style turbo navigation

PythonUltra should keep the original PyEditorRC interaction model rather than the abandoned staged/timer experiment.

- Held `UP`, `DOWN`, `LEFT`, `RIGHT`, and `DEL` repeat after the original PyEditorRC delay.
- The initial repeat threshold is 20 polling cycles.
- While already scrolling, the threshold becomes 6 and the repeat counter resets to 5.
- `is_scrolling` enables a lightweight plain-text draw path during rapid movement so syntax highlighting does not make navigation feel slow.
- Releasing a scrolling key restores the normal full-quality redraw path.
- Turbo can be toggled from `SHIFT + VARS` while preserving the jump commands and editor-style controls already added to PythonUltra.

## Files viewer and terminal handoff

The UI4 target remains:

- `Files -> OPEN` wraps long text instead of clipping it at the right edge.
- Running a `.py` file from Files returns control to the native terminal so printed output and tracebacks are visible.
- Running from inside the editor must not execute the script a second time when control returns to Files.

## PicoC inside PythonUltra

PicoC is now planned as a native secondary runtime inside `PythonUltra.g3a`, not as a separate Utilities add-in.

The uploaded `utilitiesC.g3a` is the compatibility/reference implementation. It confirms a PicoC v2.1-based calculator build, but PythonUltra should not transplant raw machine code from that add-in. The maintainable approach is to compile PicoC source directly into PythonUltra and adapt its platform layer for the fx-CG50.

### Integration goals

- Keep MicroPython and PicoC as two runtimes inside one add-in.
- `.py` files run through MicroPython.
- `.c` files run through PicoC.
- Reuse the existing PythonUltra Files browser instead of creating a second file manager.
- Reuse the PythonUltra editor for `.c` files, with C-oriented syntax behavior added incrementally.
- Reuse the native terminal/output path for PicoC `printf`, errors, and program output.
- Add an interactive `picoc>` mode after file execution is stable.
- Route PicoC allocation through calculator-appropriate memory hooks and measure both RAM use and final G3A growth.
- Keep PicoC isolated enough that an interpreter failure cannot corrupt the MicroPython runtime state.

### Context-aware catalog

The `SHIFT + 4` catalog should eventually become language-aware:

- In Python editing mode, show Python modules and their members as it does now.
- In C/PicoC editing mode, show C/PicoC categories such as `stdio`, `stdlib`, `math`, string functions, memory functions, and calculator-specific functions that are actually compiled into the PicoC runtime.
- Selecting a C entry should insert the correct function, constant, or type syntax at the cursor.
- The C catalog should be generated from the functions actually enabled in the PythonUltra PicoC build so documentation and runtime capabilities stay aligned.

### Documentation

PicoC support should be included in the same documentation philosophy as PythonUltra:

- document the supported C subset and enabled library calls;
- document calculator-specific functions and limitations;
- expose help text from within PythonUltra where practical;
- keep a generated reference in the build artifacts;
- measure the binary cost of embedded runtime documentation separately from the external documentation ZIP.

## Regression requirements

Future builds should protect at least these hardware-facing behaviors:

- `SHIFT + 4 -> module -> member -> insertion` works and punctuation is literal;
- `EXIT` backs out one catalog level at a time;
- dirty editor buffers show `Unsaved Changes!` and support both `Cancel` and `Ignore & Proceed`;
- PyEditorRC-style turbo remains responsive;
- Files OPEN wraps long lines;
- running a script from Files/editor hands output to the terminal without double execution;
- pygame/color-key and py3d rendering remain correct on both old and newer fx-CG50 display hardware.

This document is the design reference for these behaviors while the UI4 baseline is stabilized and before the PicoC runtime is merged.
