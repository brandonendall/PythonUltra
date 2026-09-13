# Motion demo, editor input and dark-mode correction: run #132

The user reported a white screen when running the run131 color-key demo and
white canvas around dark-mode Catalog dialogs. This candidate corrects those
reports and the previously reported editor keys/repeats.

**2026-09-12 follow-up:** the user confirms run #131 works flawlessly after
moving `import gint` to the top of the demo. See [the updated run131
receipt](colorkey-run131.md). This confirms the color-key fix; run132's editor
and dark-mode changes still require their own calculator checks.

## Verified build

- [Successful fx-CG50 run #132](https://github.com/OffCamera-Civilman/PythonExtra-CG50/actions/runs/34698081817).
- Source: `49964644b233fa131c380c1b5d528e32f4e80c90` on `cg50-new-display`.
- `PythonUltra-CG50-run132.g3a`: 447,228 bytes.
- SHA-256: `9bbda5c68da8a5643f90f230596a5fc038a216ebbf2b7e66de1edf4ed12e030a`.
- GitHub artifact ZIP SHA-256:
  `6e5be71bce7162d7312c2077e69bba96949e1b1936955b1ae341dbd89fed88c0`.
- Matching module-reference ZIP SHA-256:
  `34f5e48f827d972f756e4c18761628603f8cc504581b65a973465003564b8077`.
- Both embedded icons still match the supplied run130.1 pixels exactly.

## White-screen cause and fix

The original demo imported gint inside the animation loop, after sprite
drawing. `MICROPY_MODULE_BUILTIN_INIT` is enabled, `mp_module_get_builtin()`
invokes the module initializer, and `modgint___init__()` clears VRAM white and
resets the font. This made the demo erase each frame. This was an error in the
supplied demo. The later user report above supplies the hardware confirmation
for run131 with the corrected import order.

The corrected script imports gint before initialization/drawing. A regression
runs the actual shipped script while simulating the port's repeated import
initialization; it failed with the old script and passes with the corrected
script. Native keyed drawing and transform/clipping fixes from #131 remain.
The corrected script also works on run131 without replacing the add-in.

## Dark backgrounds and dialog font

GitHub Dark's editor/Files canvas and bars are now black, consistent with the
other dark palettes. Catalog, Info and Symbols clear the entire canvas black
in dark mode, including outside the colored menu border. Native scene rendering
also follows the dark/light background. Selection and configured border colors
remain visible; user graphics are not recolored and light-mode canvases remain
light. Popup font selection happens after the final gint import, preventing
its initializer from silently restoring a larger default font.

## Editor input

- F6 is labeled Sym and opens Symbols; SHIFT+VARS opens Style.
- In alpha mode, SHIFT reverses the next character's case. The a/A indicator
  shows the case that will be inserted. SHIFT+ALPHA retains uppercase lock.
- Shifted alpha keys type letters, including M/N/O/P on number keys. Numeric
  mode retains SHIFT+8 selection, SHIFT+9 paste and SHIFT+4 Catalog shortcuts.
- Filename/find inputs also support case indication and F6 Symbols.
- The reader drains queued releases before deciding whether to repeat.
  Repeated arrows/delete coalesce to one action, and real key presses keep
  their order; releasing an arrow no longer replays the accumulated repeats.

## Validation and remaining calculator checks

All existing prepared runtime regressions pass, including six Pygame color-key
tests, editor queued-event/modifier/shortcut scenarios, dark/light popup draws
and the repeated-import font reset. The real MicroPython smoke also passes the
input-reader/case checks alongside ZIP/editor/RC/Catalog behavior. The target
compiler/linker, module-reference generator (43 modules, 1,283 entries, zero
missing descriptions), G3A length/checksum/source-marker tests and icon hashes
pass. Hardware confirmation is still required:

1. Install the run132 G3A and replace the old `colorkey_motion.py` with the one
   in this bundle. Run it; expect a blue grid and moving red/cyan sprites.
   F1 toggles transparency, EXIT quits. Then test the original BMP game.
2. In dark mode open Catalog, Info, Symbols, Files and the editor. Confirm black
   canvas inside/outside dialogs and no white margins. Check light mode too.
3. In the editor press ALPHA, SHIFT, then an alphabetic key. Confirm A is shown
   and an uppercase letter appears. Check F6 Sym and SHIFT+VARS Style.
4. Hold an arrow for two seconds, release it, and confirm immediate stopping.
   Check small/normal/large text and filename/find inputs.

The master list keeps hardware verification open. ZIP compression hangs,
long-text navigation, runtime help/docstrings, adjustable date/time with true
file timestamps, PicoC and the later icon revision remain separate tasks.
