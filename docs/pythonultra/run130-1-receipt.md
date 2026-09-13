# User-supplied PythonUltra run130.1

Received from the user on 2026-09-12 as `PythonUltra-CG50-run130.1.g3a`.
This receipt identifies the actual supplied binary, without treating a
filename suffix as a GitHub Actions run number or claiming a hardware pass.

| Field | Observed value |
| --- | --- |
| Size | 446,112 bytes |
| SHA-256 | `68d6826c72c16559952ceeae351a0aab039864456704803233c6fd5a9522a61d` |
| App name | PythonUltra |
| Embedded build ID | `3f2b5e2a7f00` |
| Runtime banner | `3.4.0; MicroPython 3f2b5e2-dirty on 2026-09-08` |
| G3A metadata date | `2026.0908.0231` (timezone not encoded) |
| File type and three size fields | Pass |
| Code-word checksum | Pass |
| Whole-file checksum and matching footer | Pass |
| Selected/unselected icons | Identical 92 x 64 RGB565 images |
| Icon raw-pixel SHA-256 | `3671e810ec3a8746b18e5e65b03c3783867e288b6a1acc9bd984e7784acc873c` |

The icon is extracted losslessly to [run130-1-icon.png](../../logo/run130-1-icon.png).
It depicts a red/metallic snake around a PU emblem on black. Both icon slots
contain this same image. It is the reference for the user's requested later
dark-gray-background/black-letter-accent revision, not that revision itself.

## Comparison with CI run130

CI run130's binary has 445,648 bytes and SHA-256
`f0840f862598fb47e53382de18fe013e505c2c9aa2c4f6b1a426bd9bf1537bad`.
The supplied run130.1 file is 464 bytes larger. Both the icon data and the
executable/data payload differ; it is not simply the old binary renamed.

New readable strings include:

- `set startup=terminal` (run130 contained `set startup=files`).
- `set menu_border=red` and a comment identifying red as the omitted default
  (run130's template referenced cyan).
- `UP/DN scroll  +/- page`.

These are evidence of embedded settings/UI text, not proof that the related
behavior works. They are preservation/reconciliation targets for the next
source audit. The `-dirty` banner also occurs in ordinary CI builds because
the build runs source-preparation scripts; it does not uniquely identify
which additional edits produced run130.1. Recover the exact source/diff before
claiming every change has been recreated. Do not close the reported editor,
ZIP, sprite, help or timestamp bugs based on binary inspection.

The delivered module-reference ZIP describes the prepared repository source
at `3f2b5e2a7f00`, not a proven reconstruction of this separately modified
binary. Update its RC/UI details when those modifications are reconciled.

## Reproduction notes

Read the original file without changing it. Decode the inverted first 32
header bytes; compare the three file-size fields with the actual byte count.
The code-word checksum is the low 16 bits of the sum of eight big-endian
16-bit values at offset `0x7100`. The whole-file checksum sums original
on-disk bytes `[0,0x20)` and `[0x24,EOF-4)`; compare with the big-endian field
at `0x20` and the last four bytes.

The two icons are `92*64*2` bytes at `0x1000` and `0x4000`. Decode pixels as
big-endian RGB565. The saved PNG expands 5/6-bit channels by bit replication;
converting it back to RGB565 reproduces every source pixel exactly.

Format/checksum implementation references:
[fxSDK g3a.h](https://github.com/lephe/Fx-SDK/blob/dev/fxgxa/g3a.h),
[fxSDK util.c](https://github.com/lephe/Fx-SDK/blob/dev/fxgxa/util.c), and
[fxSDK icon conversion interfaces](https://github.com/lephe/Fx-SDK/blob/dev/fxgxa/fxgxa.h).
