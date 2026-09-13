# PythonUltra master list

Shared running task list for `OffCamera-Civilman/PythonExtra-CG50`, branch `cg50-new-display`.
Reconciled through 2026-09-12 against source, build patches, tests, run #135 at `f718931c7836`, and user hardware reports. This file is the canonical task list; update it with every feature/fix handoff. Never infer hardware success from a green compiler run or from a Catalog entry alone.

## Status rules

- **Verified**: the specific behavior was confirmed on the physical calculator.
- **Implemented**: integrated source/build exists; scope or remaining verification is stated below.
- **Active fix**: code exists but hardware reports show a defect. A local or CI pass does not close it.
- **Remaining**: not integrated, or only part of the requested functionality exists.

## September 8–12 hardware feedback and documentation handoff

The user supplied `PythonUltra-CG50-run130.1.g3a` on 2026-09-12. Its size is
446,112 bytes, and its embedded ID is `3f2b5e2a7f00`, dated 2026-09-08.
Header sizes and both checksum forms pass. This is a distinct user-supplied
build; the subsequent source-based color-key candidate is CI run #131 below.
See [the binary inspection receipt](docs/pythonultra/run130-1-receipt.md).
The exact embedded icon is preserved in `logo/run130-1-icon.png`.
Readable strings identify terminal startup and red menu-border RC defaults;
do not silently revert these while repairing the source. Complete source
provenance for the modified build remains unresolved.

- [ ] Editor: SHIFT in alpha mode must show and enter uppercase; SHIFT+VARS
  opens Style, F6 opens Symbols (label Sym); cursor repeats stop on release.
  Run #132 implements these controls and drains releases before acting
  on a coalesced repeat. Typed key presses retain their ordering; tests cover
  shifted alpha letters on numeric shortcut keys and filename/symbol prompts.
  The real MicroPython input smoke and calculator build pass; hardware pending.
- [ ] ZIP: reproduce and fix the 42,074-byte compression hang; keep failed
  output cleanup and standard archive round trips.
- [x] Pygame color-key fix: user confirms run #131 works flawlessly on the
  calculator after moving `import gint` from the animation loop to the top of
  `colorkey_motion.py`, immediately after `import pygame` (2026-09-12 note).
  The white screen was the demo's repeated-import VRAM clear. Run #132 already
  ships the corrected script. Native clipping/transform tests also pass.
  This hardware report does not specify OS/display revision or measured FPS.
- [ ] Files Open: wrap long text and make the entire file navigable.
- [ ] Dark themes: black canvas/dialog backgrounds across all screens.
  Run #132 sets dark editor/Files canvases and bars to black, clears the
  full Catalog/Info/Symbol modal canvas (including outside the colored border),
  and applies the native theme to the whole scene. Also select the popup font
  after the final gint import, which otherwise resets it. Light themes and
  user-drawn game colors retain their own palettes. Hardware check pending.
- [ ] Icon: lighter dark-gray background and black accents around letters.
  Use the recovered run130.1 snake/PU emblem as the artwork reference.
- [ ] Runtime documentation hardware acceptance: source now exposes useful
  help(function) and function.__doc__, including py3d.vec3, via the shared
  ROM reference. Real MicroPython tests cover native/frozen functions, classes,
  bound methods and import-free lookup. Ship the verified candidate and test
  help(vec3), vec3.__doc__, math.sqrt and Surface.set_colorkey on the calculator.
  Build #135 passes (630,404 bytes); see [the runtime-help receipt](docs/pythonultra/runtime-help-run135.md).
  Arbitrary user-defined function docstrings are not retained by the compiler.
- [x] Deliver a ZIP containing a plain-text reference for EVERY bundled module,
  with purpose, examples, exact supported syntax and function/method details.
  Keep the source and generation/check command in this repository. Update the
  references and ZIP whenever a library or public functionality is changed.
  Updated for run #132: `PythonUltra-Module-Documentation.zip`, 43 module and
  submodule text files, 1,283 inventoried member/alias/constant names. Generated
  from the prepared source at `49964644b233`, including native color-key drawing,
  the corrected import guidance and editor shortcut/case semantics.
  Runtime help now uses the same descriptions; its hardware gate is above.
- [ ] Explain version labels and changes: the source is MicroPython
  1.25.0-preview; 3.4.0 in sys.version is a Python compatibility label.

PicoC, adjustable date/time and truthful persistent file timestamps remain
open below. The new reports do not mark those capabilities completed.

## Current correction release

Candidate **run #132** passed GitHub Actions on 2026-09-12, commit
`49964644b233fa131c380c1b5d528e32f4e80c90`.
Download: `PythonUltra-CG50-run132.g3a`, **447,228 bytes**.
SHA-256: `9bbda5c68da8a5643f90f230596a5fc038a216ebbf2b7e66de1edf4ed12e030a`.
[Build and artifact](https://github.com/OffCamera-Civilman/PythonExtra-CG50/actions/runs/34698081817).
Corrects the shipped motion demo's white-screen import error, editor key
handling, black dark-mode canvases and modal font reset. All prepared runtime
regressions, module-reference generation and G3A integrity checks pass. Hardware
acceptance remains open. [Receipt and test steps](docs/pythonultra/ui-run132.md).

Previous color-key candidate (original demo reported white on hardware):

Candidate **run #131** passed GitHub Actions on 2026-09-12, commit
`7f90654337b28f6fcba6b7f73fe424aeffd090f6`.
Download: `PythonUltra-CG50-run131.g3a`, **446,696 bytes**.
SHA-256: `d3eedbb3cc979f01ce42aaf17290065568a94196888e04cb62aeb617f95cca0c`.
[Build and artifact](https://github.com/OffCamera-Civilman/PythonExtra-CG50/actions/runs/34697047264).
This candidate adds a native RGB565 color-key blit, correct source/destination
clipping, and preserved transparency keys in transforms. All host regressions,
target compilation/linking, G3A checksums, and documentation coverage checks
pass. Both icon slots match the supplied run130.1 pixels exactly. Hardware
movement remains the acceptance gate; other reported defects remain open.
See [the color-key handoff and test steps](docs/pythonultra/colorkey-run131.md).

Previous correction baseline:

Candidate **run #130** passed GitHub Actions on 2026-09-07, commit
`c6b74e611d62abd3041f604d835a253230ccb027`.
Download: `PythonUltra-CG50-run130.g3a`, **445,648 bytes**.
SHA-256: `f0840f862598fb47e53382de18fe013e505c2c9aa2c4f6b1a426bd9bf1537bad`.
[Build and artifact](https://github.com/OffCamera-Civilman/PythonExtra-CG50/actions/runs/34140659391).
Editor/ZIP/RC/Catalog/color/timestamp regressions and native seek/tell tests pass;
the ZIP round-trip and editor/RC scenario also passed in a real MicroPython host
interpreter. **Hardware confirmation of these corrections remains open.**

| Item | Status | Evidence / acceptance gate |
| --- | --- | --- |
| Editor proportional-font spacing and small/normal/large layout | Active fix | Photos show gaps/clipped bars. Measure gint glyph advances, keep chrome small, verify all sizes on hardware. |
| Editor ALPHA/SHIFT, filename/search/symbol popup input and safe launch/return | Active fix | `7c88b79` changed the handoff to raw events; editor opens in current photos. Verify typing/modifiers and repeated enter/exit. |
| Editor New/Open/Save/Find/Run, multiline clipboard | Active fix | Preserve buffers on failed open/save, prevent existing-file overwrite by New, and execute Run only once. |
| Standard ZIP create/extract | Candidate fixed; verify hardware | User reported `ValueError('truncated ZIP')`. The no-op native seek/tell implementation is replaced; tests cover files, nested folders, CRC, failed-output cleanup and preservation of existing destinations. Old malformed archives may need recreating from their originals. |
| RC-controlled startup | Candidate fixed; verify hardware | The unconditional Files launcher is removed. Missing setting -> Files; `set startup=files` -> Files; `set startup=terminal` -> Terminal. |
| Catalog insertion into terminal/editor | Active fix | F3 discarded the selection; editor inserted only an unqualified member. Insert e.g. `numpy.array` at the cursor, preserve existing input, cancel without insertion, and never execute automatically. Verify EXE/numbered choices on hardware. |
| Configurable menu border color | Implemented; verify hardware | Named color, `#RRGGBB` or RGB565 integer in RC. Preserve the supplied run130.1 red fallback and terminal-startup template; existing RC choices still take precedence, and absent/invalid startup in an existing RC falls back to Files. |
| File information Modified field | Active fix | User photo shows an implausible integer. Initialize native stat fields, display a valid stored date/time or Unavailable, and complete the clock/timestamp work below. |
| Filesystem reset regressions | Active fix / verify | World-switch corrections exist (`aa09418`, `c447fca`, `d38dcac`). Retest ls/listdir, mkdir, rename/move, remove/rmdir, stat and ZIP on both revisions. |
| Numbered deliverables | Implemented | Run #132 uploads `PythonUltra-CG50-run132.g3a` with a checksum, source commit, corrected motion demo and matching module reference; continue this naming for future runs. |

## Already built — do not schedule from scratch

| Capability | Status | Cross-reference / what remains |
| --- | --- | --- |
| PythonUltra name and new-screen compatibility | Verified foundation | Run #33 starts/displays on older OS 3.7 and newer OS 3.81.0 hardware; see README. Newer features still need their own checks. |
| Interactive Python REPL | Implemented | `ports/sh/main.c`, `pyexec.c`, `widget_shell.c`; preserved alongside the terminal. |
| Compact Pygame | Implemented; base build hardware-tested | Frozen `modules/pygame`, `tests/ports/sh/pygame_compat.py` and `pygame_cg50_regression.py`. Surface/Rect, drawing, display, keys/events, fonts, images, transforms, Sprite/Group/GroupSingle and collisions. No sound/network/SDL windows. |
| Pygame game clock | Implemented | `pygame.time.Clock` includes frame timing. This is not a date/time settings interface or a standalone `time.Clock`. |
| BMP color-key transparency | Verified by user on run #131 with corrected demo | 2026-09-12: user moved import gint to the top after import pygame and reports flawless operation. Run #132 already ships that correction. Six regressions cover native pixels and the demo; OS/revision and measured FPS were not supplied. |
| Compact NumPy matrices/vectors | Implemented | Frozen `modules/numpy`, `apply_pythonultra_features.py`, `numpy_compat.py`: transpose/inverse, dot/matmul, cross/norm/normalize/lerp and array helpers. No desktop-NumPy claim. |
| Native filled triangles | Implemented | `modgint.c::modgint_dtriangle`, `gint.dtriangle(...)`. |
| py3d first engine | Implemented | `modules/py3d`, `py3d_compat.py`, rotating-cube demo: transforms, projection, back-face culling, painter sorting, simple lighting, native rasterization, wireframe. |
| Restricted ctypes | Implemented | `modctypes.c`: scalar conversions, managed buffers/byte operations, restricted call interface; not unrestricted desktop ctypes. |
| JSON, os, sys/path and I/O | Implemented, file-safety fixes active | `mpconfigport.h`, `modos.c`, `fdfile.c`, `pathutil.c`; includes JSON encoding/decoding and virtual cwd. Basic file writing exists. |
| Basic random | Implemented | `MICROPY_PY_RANDOM` and `MICROPY_PY_RANDOM_EXTRA_FUNCS`: seed/getrandbits/randrange/randint/choice/random/uniform. Only missing requested APIs/testing remain. |
| Files create/rename/delete and general text files | Implemented, safety verification active | `modules/pyfiles`: arbitrary extensions, folders, text preview, file actions. |
| Files multi-select/cut/copy/paste | Implemented | `09f2d3e`, `cbe0b99`; files and folders, clipboard and selection workflows. |
| Files filename search and sorting | Implemented | `09f2d3e`, `bc7acfb`: name/type/size orders. Recursive/content search remains optional. |
| File information | Verified screen; timestamp defective | Photo confirms filename/full path/type/size/permissions/actions render. `ca37896`; fix Modified rather than rebuild the screen. |
| SHA-256 and SHA-1 file checksums | Implemented | `modchecksum.c`, build wiring, `6c3adc8`, `ca37896`. MD5 not added. |
| Virtual rwx permissions | Implemented | `modules/pyperm`, terminal chmod and Files/editor checks; not native POSIX filesystem protection. |
| Linux-like terminal and help | Implemented | `modules/pyterm`: ls/cd/pwd/mkdir/touch/rm/rmdir/mv/cp/cat/echo/clear/chmod/python/zip/unzip/edit/files/modules/info/version/alias/unalias/source/history/font/theme/rc. |
| Script arguments, aliases, history, RC, font/theme | Implemented, startup defect active | `sys.argv`, persistent history, UP/DOWN recall, source/rc reload and shell font/theme bridge. |
| Python help flag aliases | Implemented | `bc1fba8`: -h, --help, --h, -help. |
| Catalog module/function listing | Verified module list; function listing implemented | User Catalog photo, `modules/pythonultra::catalog_ui`; individual usage pages remain. |
| Editor themes, symbols, plain-text editing | Implemented, active correctness fixes | Five palettes and runtime ASCII symbol picker exist; small/normal/large rendering and editing safety under repair. |
| UI tabs/popups and black icon base | Implemented, polish remains | `815ff87` modal style, Files softkeys, `1927ad2`/`f655d93` icon preprocessing. Verify contrast, label spacing and OS icon safe area. |
| CI build, G3A smoke checks, user guide | Implemented | `.github/workflows/build-cg50.yml`, `ports/sh/PythonUltra_User_Guide.txt`; enforces <2,000,000-byte target. |

## Remaining capabilities and follow-up work

### Adjustable clock, date and truthful file timestamps

- [ ] Provide an on-calculator date/time display and controls to set year, month, day, hour, minute and second (user clock-screen reference).
- [ ] Validate date ranges, leap years and rollovers; read back the clock and verify persistence after leaving/restarting the add-in.
- [ ] Make wall-clock time APIs reflect the date and time; current `modtime.c` uses `rtc_ticks()/128` (seconds since midnight), not an epoch date/time. Audit `monotonic` units separately and keep elapsed game timing independent of manual clock changes.
- [ ] Connect file creation/save/modification to the real supported timestamp backend. Verify whether the calculator OS stores mtime before promising native timestamps; document any PythonUltra-managed fallback explicitly.
- [ ] Show Modified as a readable date and time, not raw integers. Show Unavailable for absent/invalid metadata; never stamp old files with the current time as if that were their original modification date.
- [ ] Test save -> inspect Modified -> restart -> inspect again, on both calculator revisions. Reformatting an invalid value does not satisfy this requirement.

### Editor and Files

- [ ] Editor bounded undo/redo; select all/deselect; clear/delete workflows.
- [ ] Hardware-verify fonts; keep broken JetBrains editor options hidden until glyph data is fixed/verified. Terminal JetBrains choices also require verification.
- [ ] Storage-free-space display.
- [ ] Files BMP/PPM preview. Pygame loading exists but is not a Files preview screen.
- [ ] Memory-conscious baseline JPEG preview; no full-screen heap buffers.
- [ ] File-info Copy/Move/Delete shortcuts where absent; MD5 only if footprint is acceptable.
- [ ] Optional recursive/content search subject to memory limits.

### Python/module and developer features

- [ ] Finish help/Catalog member pages: actual syntax, description, example and honest supported subset.
- [ ] Audit extra random APIs against the examples; basic random already exists.
- [ ] Resolve standalone `time.Clock` compatibility requested in notes (Pygame Clock already exists).
- [ ] Add compact `datetime`, `pathlib` and `csv` capabilities; no integrated public modules found in current target manifest.
- [ ] Integrate uploaded turtle/matplotlib-style functionality as built-ins. `modules/cg/turtle.py` and `matplotl.py` source exists, but current fx-CG50 manifest does not freeze it. Compare uploaded API before deciding reuse/native implementation; do not claim full desktop matplotlib.
- [ ] Calculator debugger: define minimal supported stepping/breakpoint/inspection workflow.
- [ ] PicoC: retained user goal; no current integration found. Confirm the intended C-interpreter subset, memory budget, licensing and Files/terminal/editor entry points before implementation. Earlier detailed scope was not recovered in this audit.
- [ ] Further shell improvements only for identified gaps; existing shell/RC/history/aliases are not unbuilt work.

### py3d continuation and polish

- [ ] Near-plane triangle clipping (current engine skips crossing triangles).
- [ ] Movable camera/view transforms, mesh loading and frustum culling.
- [ ] Profile on hardware, then move justified hot paths to C.
- [ ] Consistent Casio-style F1-F6 slots, readable dark/light contrast, visible secondary actions and final icon safe-area check.

## Release and collaboration guardrails

- Keep PythonUltra under the 2 MB build target and respect actual calculator heap limits (current Pygame BMP loader is deliberately capped at 56x56).
- Retest older/newer fx-CG50 OS/display revisions after native I/O/display/input changes.
- Record commit, Actions run, byte size/checksum, delivered filename and exact hardware result for each handoff.
- Repository owner: `OffCamera-Civilman`; co-collaborator: Brandon Endall (`@brandonendall`). Preserve upstream/community attribution.
- Utilities v2.1 and Geometry/Casio menus are functionality/UX references. Do not copy incompatible third-party source without a project licensing decision.
