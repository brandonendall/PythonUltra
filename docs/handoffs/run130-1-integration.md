# run130.1 integration into PythonUltra

## Source and baseline

- Target: `brandonendall/PythonUltra`, based on `cg50-new-display` at
  `71874b9b5ee65b0fa6171a60abf7ec53d23a4805`.
- Original repository: `OffCamera-Civilman/PythonExtra-CG50`; its development
  head when inspected was `3f2b5e2a7f00b5d0a175904f6e5a5543080ed6e0`.
  PythonUltra contains that source plus the dark-information/red-default commit.
- Original project handoff: [issue #2](https://github.com/OffCamera-Civilman/PythonExtra-CG50/issues/2).
- The user supplied `PythonUltra-CG50-run130.1.g3a` (446,112 bytes) and reports
  that Brandon built it from a clone on another server, tested it himself,
  and confirmed it works. Preserve it as the Brandon-tested working baseline.
- Baseline SHA-256:
  `68d6826c72c16559952ceeae351a0aab039864456704803233c6fd5a9522a61d`.
- Embedded identification: `MicroPython 3f2b5e2-dirty on 2026-09-08` and
  `2026.0908.0231`. The server's local source changes were not attached, so
  exact source-to-binary reproduction remains unverified. This does not
  invalidate Brandon's reported working hardware result.
- The unchanged baseline is in `releases/reference/`; the original written
  request is `docs/handoffs/run130-1-request.txt`. These are reference inputs,
  not outputs of the new clock implementation.

## Integrated changes

- Retain the existing red menu-border default and startup, display, editor,
  Files, ZIP, Catalog, game and shell functionality.
- Correct the information frame's `drect_border` fill/border argument order,
  clear the full page to the selected background, and retain scrollable text.
  Existing Catalog/editor popup behavior is unchanged.
- Use the supplied 92x64 RGB cyber-snake icon, byte for byte, for selected,
  unselected, release and development icons. Both local and CI builds use the
  tracked PNG; CI no longer replaces it with a JPEG fetched from `main`.
- Add **Info -> F2 Date/Time**, plus the terminal `clock` command. Select a
  field with UP/DOWN or EXE; type digits or use +/-; F1 saves and EXIT cancels.
  No clock write occurs while editing or cancelling. Save validates and reads
  the hardware back, accepting a one-second rollover.
- Add `time.set_datetime((year, month, day, hour, minute, second))` with native
  validation before narrowing or writing RTC values. A matching 8/9-field
  time tuple is also accepted; supplied weekday/yearday fields are ignored.
- Provide `time.time()`, `time.time_ns()`, `time.localtime([seconds])`,
  `time.gmtime([seconds])` and `time.mktime(tuple)` using the same Unix epoch.
  Supported calendar range is 1970–2099. `time()` returns integer seconds;
  `time_ns()` uses nanosecond units with one-second resolution. Conversion
  uses unsigned seconds so dates after 2038 work on the 32-bit target.
- `mktime` accepts 8/9-field tuples and rejects invalid dates rather than
  normalizing them. `localtime`/`gmtime` accept integer seconds. There is no
  timezone/DST database; both represent the calculator's configured civil
  time without a timezone adjustment. No UTC synchronization is implied.
- The setting writes the hardware RTC, which continues independently of the
  add-in. There is no stale config timestamp restored at launch. Restart
  persistence and operation on both display revisions require hardware
  confirmation for this new candidate.
- Fix `time.monotonic()` to return seconds instead of nanoseconds. The
  dependency audit found fxlibc `clock()` also derives from `rtc_ticks()`, so
  replace that source for `monotonic` and `ticks_*` with a reserved 1 ms TMU
  timer and an atomically read 64-bit counter. Pygame continues using ticks.
  No RTC value or RTC adjustment enters the elapsed counter. This uses one
  TMU while the add-in is active; timer exhaustion raises EBUSY. `ticks_us`
  has microsecond units but 1 ms resolution, and `ticks_cpu` counts ms.
  Time suspended outside the add-in or with interrupts masked is not
  guaranteed to be counted; verify frame timing and world switches on device.
- Keep absent filesystem timestamps as **Unavailable**. No old file is
  stamped with the current time. OS modification-time support remains a
  separate hardware/backend task.

## RTC dependency detail

The workflow pins gint to `badbd0fd2bd8ac796fd55d49b93691741bd8a139` plus its
existing display backport. At that revision `src/rtc/rtc.c` directly transfers
the hardware RMONCNT (1–12); `include/gint/rtc.h` misleadingly describes the
month as 0–11. The adapter follows the implementation's register convention.
The RTC driver saves/restores control registers across gint transitions, not
the date/time values. Verify January/December, midnight and leaving/restarting
the add-in on hardware before calling the new clock verified.

## Validation and release gate

Local validation:

- Actual C calendar/RTC adapter compiled with `-Wall -Wextra -Werror` against a
  simulated RTC; all 47,482 dates from 1970 through 2099 matched host calendar
  arithmetic. Leap days, second/day/year rollover, the 2038 boundary and
  rejected input without writes passed.
- Clock UI save/cancel, dark/light mode, range validation, failed readback and
  midnight readback rollover passed with simulated time/key events.
- Full `pythonultra-runtime-fixes` gate passed: editor, ZIP round trips,
  RC/startup, native seek/tell, Catalog, timestamps, Pygame, NumPy, py3d and
  feature checks. The build's source-preparation scripts run once; subsequent
  test/compile passes use `PYTHONULTRA_RUNTIME_PREPARED=1` as CI already does.
- Modified Python modules compile with this repository's MicroPython bytecode compiler.
- Supplied icon dimensions, RGB mode and black corners checked; all generated
  icon files copy the original bytes without resizing or recoloring.
- `.g3a` is explicitly binary in Git attributes, and staged baseline bytes
  match the supplied file and its SHA-256 exactly.

These are host tests, not a new cross-compiled G3A or hardware certification.
Use the build workflow for the candidate, record its commit, Actions run,
filename, byte size and SHA-256, then test on both calculator revisions.
Numbered candidate names come from this repository's Actions counter, which
is separate from the original repository's run counter. Do not relabel the
supplied run130.1 baseline as a newly built candidate.

Hardware acceptance:

1. Check the icon in the OS menu and dark/light Info, scrolling, configured
   border colors, and returning to Files/terminal/editor.
2. Set all six fields; reject invalid dates; check cancel leaves time unchanged.
3. Check leap day, midnight/month/year rollover, and dates after January 2038.
4. Leave/reopen the add-in, restart the calculator, and check that the clock
   continued to advance. Record hardware/OS revision and exact result.
5. Change the wall clock forward/backward and verify Pygame/ticks timing.
6. Recheck Files/ZIP/editor and truthful Modified display; unavailable native
   metadata must remain unavailable.

Preserve attribution to OffCamera-Civilman, Brandon, PythonExtra, MicroPython,
gint, JustUI and the Planete Casio contributors.
