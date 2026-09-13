# PythonUltra independent maintenance migration

## Repository snapshot and preservation

Inspected 2026-09-13 before destination changes:

| Repository | Branch | Commit |
| --- | --- | --- |
| brandonendall/PythonUltra | main | 1ee197f287a224f7155dc6c14779bd3f2ff47aca |
| brandonendall/PythonUltra | cg50-new-display | 71874b9b5ee65b0fa6171a60abf7ec53d23a4805 |
| brandonendall/PythonUltra | grace/integrate-run130-1 | 71874b9b5ee65b0fa6171a60abf7ec53d23a4805 |
| OffCamera-Civilman/PythonExtra-CG50 | main | 1ee197f287a224f7155dc6c14779bd3f2ff47aca |
| OffCamera-Civilman/PythonExtra-CG50 | cg50-new-display | 43b3796e155bf2a3243eda583c4b7ca8e7adb701 |

Development histories diverged after `3f2b5e2`: destination had one unique UI
commit and upstream had ten subsequent commits. The migration merges both
histories on `migration/independent-cg50`; it does not replace main or rewrite
existing branches. PythonUltra remains in GitHub's fork network until the owner
chooses detachment. Builds and maintenance do not depend on that detachment.

The original uncommitted checkout was left intact. Its complete source edits,
including untracked elapsed timer files, were preserved separately on
`archive/local-run130-1-work` at
`71ac1d0e59a7e568df860d431ba2a941e27e4022`. That branch contains experimental
clock/RTC/timer work and earlier claims of host validation; it is not a tested
calculator release and is deliberately not enabled in this migration. This
avoids introducing a hardware timer allocation and RTC behavior into UI/build
migration without calculator acceptance. The alternative icon is preserved there.
The migration uses upstream's icon recovered from the known-good binary.

Brandon's separately built, hardware-tested 130.1 is retained at
`releases/reference/PythonUltra-CG50-run130.1.g3a` on the archive branch:
446,112 bytes, SHA-256
`68d6826c72c16559952ceeae351a0aab039864456704803233c6fd5a9522a61d`.
Its exact dirty server source is unavailable; no GitHub commit is claimed to
reproduce that binary exactly.

## Deliberate source choices

- Retain native Run 131 color-key drawing and transparency through transforms.
  Run 131 **passed physical CG50 testing**. The initial white screen belonged to
  a demo importing gint in its loop, fixed by moving `import gint` immediately
  below `import pygame`. It was not a broken Run 131 add-in.
- Include Run 132 import, editor repeat/shifted-alpha, F6/SHIFT+VARS and dark
  canvas/dialog corrections. Preserve small popup font selection after the last
  gint import, because imports reset the display/font on this port.
- Preserve PythonUltra's red menu-border fallback, existing configured startup,
  terminal startup for newly created RC files (matching the recovered 130.1
  template), and its separate scrollable framed F6 Info. Existing RC selections
  remain honored; missing/invalid selections still fall back to Files.
  Correct Info's body fill/border argument order and clear its surrounding canvas
  black. Keep light-theme backgrounds and selected/colored UI accents meaningful.
- Include Run 133–135 ROM-backed module help, separately from feature scheduling.
  Lookup resolves actual objects without importing gint or calling user attribute
  hooks. Static const string objects and table reside in ROM; lookup needs no
  persistent per-entry heap copies. Normal output/lookup can still use stack and
  transient memory. Physical memory headroom and help readability remain untested.
  Real MicroPython tests cover bound/inherited/native methods, hashing/dictionary
  keys, unchanged calls, unrelated names and avoiding attribute/import side effects.
- Preserve Run 135's prepare-once pipeline: serial transformations, validation,
  runtime documentation tests, then compile with `PYTHONULTRA_RUNTIME_PREPARED=1`.
- Run 132 was a correction build, not completion of the planned Modified timestamp
  tranche. Truthful native timestamps, restart persistence and revision testing
  remain open. Unknown file metadata must remain unavailable.

## Complete GitHub Actions inventory and adaptations

Upstream main has the historical bootstrap workflow only. Its development branch
has the following five workflows; there are no composite actions or reusable
workflow calls. Every workflow is accounted for below.

| Workflow path | Upstream behavior | PythonUltra behavior |
| --- | --- | --- |
| build-cg50.yml | Build/test CG50, numbered G3A and reference ZIP | Preserved; own checkout, main/development/migration triggers and PRs; numbered matching ZIP, repository/SHA/run metadata, checksums and section sizes |
| module-documentation.yml | Transform source, generate reference/header, host runtime docs tests, upload ZIP | Preserved; own triggers plus runtime-test paths; numbered docs artifact with provenance/checksum |
| test-py3d.yml | Compact 3D regressions | Preserved; main/development/migration pushes, PRs, manual dispatch |
| apply-pygame-colorkey.yml | One-shot text patch and push directly to cg50-new-display | Replaced with native color-key regression validation; obsolete patch could regress/fail the Run 131 implementation |
| bootstrap-upstream.yml | One-shot import from Planet Casio and push to main | Replaced with source/provenance validation; source is already imported and merging is the maintained update mechanism |

All workflows use `contents: read`, Ubuntu runners and checkout v4. No workflow
pushes source, publishes releases, sends messages, or depends on OffCamera secrets.
Push triggers include `main`, `cg50-new-display`, and `migration/**`. PR targets are
main/development; `workflow_dispatch` is provided. The three main jobs use
per-workflow/ref concurrency without cancellation. A dispatch UI may not appear
until workflows are on the default branch; branch push already runs them.

Supporting automation retained:

- `ports/fxcg50/Makefile` serially runs six `ports/sh/apply_*.py` transformations
  (runtime_fixes, pythonultra_features, ui2, permissions, ui3_compat, symbols),
  generates module docs/header, compiles Python syntax, and runs pygame/native
  color-key, NumPy, py3d, editor, ZIP, RC, fdfile, Catalog, timestamp and feature tests.
- `tools/pythonultra_docs.py`, `pythonultra_doc_content.py`,
  `PYTHONULTRA_DOCUMENTATION.md`, source inventories and `docs/library` produce
  source-audited reference documents and `ports/sh/module_docs.h`.
- `tests/ports/sh/runtime_docs_host.py`, `runtime_docs_micropython.py`, and
  `doc_variant/` build/test a real Unix MicroPython against prepared calculator
  source. They do not require desktop CPython help behavior or external submodules.
- Native doc support in `py/objdoc.*`, runtime, builtinhelp, objboundmeth, py.mk
  and port config; native color-key support in modgint/colorkey and pygame; fixed
  `ports/sh/examples/colorkey_motion.py` accompanies downloads.
- Icon asset is tracked locally. JetBrains raster fonts use the pinned official
  TTF URL in `ports/fxcg50/prepare_jetbrains_mono.py` and retain its OFL license.
- Host packages: curl, git, Python/Pillow, build-essential, cmake, pkg-config,
  libusb, SDL2, libpng and ncurses. GiteaPC installs fxSDK, sh-elf-binutils/GCC,
  OpenLibm, fxlibc, gint and JustUI; JustUI's compatibility fallback is retained.
- gint base `badbd0fd2bd8ac796fd55d49b93691741bd8a139` plus R61524 backport
  `27000967d72d16f92ab54e7a10c7505ef85e2e85` are retained. The workflow records
  versions and display source/patch evidence. GNU download retries are retained.
- fxSDK cache is repository-scoped `~/.local`, keyed by OS and compatibility
  version. PythonUltra's first build must populate its own cache. Other toolchain
  components currently follow upstream install behavior and are not all locked;
  recorded versions aid diagnosis but do not guarantee bit-for-bit cold rebuilds.
- Build IDs use ports/sh Makefile git metadata. Numbered downloads use each
  workflow's own `GITHUB_RUN_NUMBER`; destination run 2 is not upstream run 132.
  Repository, SHA, ref, run/attempt, dependency versions and SHA256SUMS accompany
  calculator output. Docs-only numbering explicitly says `docs-run`.

Required settings: Actions enabled, permission to run the checkout/cache/artifact
Marketplace actions and Ubuntu hosted jobs, plus outbound GitHub, Planet Casio,
GNU and Ubuntu package access. No custom secret or repository variable appears in
these workflows. Default read-only GITHUB_TOKEN suffices. Secret values were not
requested or inspected. Releases, branch protections, required-check rules and
fork detachment are not automatically configured by this migration.

## Verification record

See `migration-verification.json` for exact workflow URLs, numbers, SHAs, results
and artifacts. A failed first destination build was a migrated YAML icon-path
error, corrected in `39569967102955fdf3438e78d606569500e0f58c`.

Local host: full runtime-fixes validation and real MicroPython runtime-doc tests
passed. Initial merge test assertion was corrected to distinguish Catalog's
existing accent frame from Info's black body. Generated/transformed sources are
build products and were not committed over their input source.

Hardware acceptance remains separate: install the newly generated candidate;
check boot on both display revisions, F1–F6 dark/light screens and dialog surrounds,
F6 Info scrolling, popup fonts, editor repeats/shifted alpha/SHIFT+VARS, Files/ZIP,
configured startup/accent, help()/__doc__ and free memory under typical workloads,
then the corrected native color-key motion demo after help. Record exact binary
checksum, OS/display revision and each result. CI success does not certify these.

## Documentation cost evidence

Upstream Run 135 was 630,404 bytes; its ELF sections were text=600,552,
data=1,168 and bss=1,984 bytes. These section sizes do not measure runtime heap
usage or maximum stack depth. The migration retains the ROM design conditionally
on CI success and leaves real calculator free-memory/workload testing open.

For comparison, upstream Run 132 was 447,228 bytes with text=417,376,
data=1,168 and bss=1,984. Run 135 added 183,176 bytes (about 179 KiB) of text/ROM
with no change in linked data or bss. This supports keeping the feature for its
help value; it does not establish calculator peak heap/stack usage.
