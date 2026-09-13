# Color-key sprite correction: run #131

**Hardware confirmation, 2026-09-12:** the user confirms run #131's color-key
fix works on their calculator. They moved `import gint` out of the
`colorkey_motion.py` frame loop to the top of the file immediately after
`import pygame` and report that it "works flawlessly." The white screen was
caused by the demo re-importing gint after drawing and clearing VRAM, not a
failure of run #131's native sprite fix. The repository already ships this
corrected import order in [run #132](ui-run132.md).

Record this as a user-confirmed pass for run #131 with the corrected script.
The note does not specify calculator OS/display revision or a measured FPS;
do not infer a test on both revisions or a separate original-game test.

The user reported that `set_colorkey((0, 0, 0))` removed the black sprite
background but movement became slow, with sprites disappearing and reappearing
partway across the screen. This candidate addresses the expensive drawing path
and related clipping/transform defects. The corrected demo is now confirmed
working by the user, as recorded above.

## Build receipt

- Source: `7f90654337b28f6fcba6b7f73fe424aeffd090f6` on `cg50-new-display`.
- [Successful calculator workflow](https://github.com/OffCamera-Civilman/PythonExtra-CG50/actions/runs/34697047264).
- File: `PythonUltra-CG50-run131.g3a`, 446,696 bytes.
- SHA-256: `d3eedbb3cc979f01ce42aaf17290065568a94196888e04cb62aeb617f95cca0c`.
- Both embedded icons reproduce the supplied run130.1 icon pixel for pixel.
- Matching reference: 43 module/submodule text files, 1,283 member/alias/constant
  names; no missing descriptions. Documentation ZIP SHA-256:
  `be1096fa5ad7a8431470251491a0db204258c76f5f979001bbe7da5e0f71283c`.
- Downloaded GitHub artifact ZIP matches its published SHA-256:
  `c5f6ca9a23b015ab339033fbfcd9cce3f45dd0de734a72790df882eb3d79300f`.

## What changed

Previously a keyed screen blit looped over every sprite pixel in Python,
calling the native pixel function separately for each visible pixel. Ordinary
opaque images already used the native image path. The new RGB565 keyed path
uses one allocation-free native call and reads the current source buffer on
every draw; buffer edits and changes of key cannot leave a cached image stale.

The native helper clips both source and destination, respects the current
display window, and handles padded/unaligned source buffers. `Surface.blit`
also crops its software and opaque paths consistently with the surface clip.
Scale, flip and rotate preserve the transparency key and alpha metadata;
rotation fills uncovered corners with the actual key, including nonblack keys.
This does not add per-pixel alpha blending.

The source also preserves the supplied run130.1 icon, red default menu border
and terminal-startup template. Existing explicit RC settings still win;
missing/invalid startup in an existing RC falls back to Files. The exact source
for every modification in the separately supplied run130.1 binary has not been
recovered; [its receipt](run130-1-receipt.md) records that limitation.

## Validation

Five focused host tests execute the actual native pixel routine: a moving
56x56 sprite at both screen edges, source/destination clipping, immediate buffer
and key edits, transform metadata, and 150 deterministic padded-buffer/extreme
coordinate cases with destination guard words. Each visible keyed screen blit
must use exactly one native call and no per-pixel Python calls.

All existing Pygame, NumPy, py3d, editor, ZIP, RC, native seek/tell, Catalog,
timestamp and feature host regressions pass. The fx-CG50 compiler/linker and
artifact upload pass. The downloaded G3A passes type, three length fields,
code-word checksum, full-file checksum/footer, source ID and native API marker
checks. Both icon-slot hashes match the supplied binary. Host tests and a green
build do not demonstrate a physical-calculator frame rate.

## Calculator acceptance test

1. Install `PythonUltra-CG50-run131.g3a` as the active PythonUltra add-in.
2. Transfer and run `colorkey_motion.py`. It needs no image files.
3. Watch the red and cyan sprites move in opposite directions over the grid.
   Their black/magenta backgrounds should be transparent. They should remain
   visible throughout the interior and clip cleanly at the screen edges.
4. Press F1 to compare key ON/OFF; press EXIT to quit.
5. Run the original BMP game with `set_colorkey((0, 0, 0))`. Confirm that the
   movement defect is gone. Record calculator OS/revision and any remaining
   behavior before closing this item on the master list.

The demo deliberately wraps from one edge to the other after a full crossing;
that restart is expected. Its 30 FPS cap is a target, not a measured guarantee.

Editor input, ZIP compression hang, long-text navigation, remaining dark
backgrounds, runtime help/docstrings, adjustable clock/file timestamps and
PicoC remain separate open tasks on the master list.
