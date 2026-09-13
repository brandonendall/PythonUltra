# PythonUltra for fx-CG50

The maintained **PythonUltra** project, derived from PythonExtra, focused on modern Casio fx-CG50 hardware and lightweight 2D/3D game development.

[![Build fx-CG50](https://github.com/brandonendall/PythonUltra/actions/workflows/build-cg50.yml/badge.svg?branch=main)](https://github.com/brandonendall/PythonUltra/actions/workflows/build-cg50.yml)

## Confirmed hardware compatibility

The `PythonUltra.g3a` produced by [GitHub Actions run #33](https://github.com/OffCamera-Civilman/PythonExtra-CG50/actions/runs/33685440342) has been tested successfully on physical fx-CG50 calculators:

| fx-CG50 configuration | OS version | Result |
| --- | --- | --- |
| Older hardware/display revision | 3.7 | Pass |
| Newer hardware/display revision | 3.81.0 | Pass |

The same add-in starts and displays correctly on both revisions. The newer-display correction eliminates the former black-screen/reset lockup.

## Project goals

1. Import and preserve the upstream PythonExtra source.
2. Restore display compatibility on newer fx-CG50 hardware/OS revisions.
3. Keep the interactive Python shell.
4. Add game-oriented functionality with minimal footprint.
5. Add a C-backed `dtriangle()` rasterizer to the gint-facing module.
6. Add a compact `ctypes`-style interface appropriate for the embedded MicroPython environment.
7. Add a NumPy-compatible numerical layer sized for the fx-CG50 rather than attempting to ship desktop NumPy unchanged.
8. Produce reproducible `.g3a` build artifacts with GitHub Actions.
9. Provide a compact, calculator-native Pygame compatibility layer for learning and game projects.
10. Provide a compact software 3D engine that uses the native triangle rasterizer.

## Compact Pygame layer

`import pygame` is built into `PythonUltra.g3a`. The first compatibility release includes:

- display setup/update, RGB565 `Surface`, `Rect`, colors and pixel access;
- rectangle, line, polygon, circle, ellipse and arc drawing;
- calculator key events, pressed-key state and an `EXIT`-to-`QUIT` mapping;
- `pygame.time.Clock`, delay and tick timing;
- text rendering through the calculator font;
- uncompressed 24/32-bit BMP and binary PPM image loading;
- image scaling, flipping and rotation;
- `Sprite`, `Group`, `GroupSingle` and rectangle collision helpers.

Audio, networking and SDL desktop-window features are deliberately omitted. The display is always the physical fx-CG50 resolution, 396×224, even if a desktop-oriented program requests another mode.

## Compact py3d engine

`import py3d` is frozen into PythonUltra. The first 3D milestone includes:

- 3D vectors with add/subtract/scale, dot product, cross product and normalization;
- 4×4 identity, translation, scaling and X/Y/Z rotation matrices;
- matrix composition and vertex transformation;
- perspective projection for the 396×224 fx-CG50 display;
- back-face culling;
- painter-style depth sorting;
- simple directional face lighting and RGB565 shading;
- filled mesh rendering through the native C-backed `gint.dtriangle()` rasterizer;
- optional triangle wireframes;
- a built-in colored cube mesh helper;
- `ports/sh/examples/cg_py3d_cube.py`, an interactive rotating-cube hardware demo.

The first milestone intentionally skips triangles that cross the near plane instead of splitting them, and uses painter sorting rather than a per-pixel Z-buffer. Those choices keep memory use appropriate for the calculator while establishing the full transform → cull → project → sort → rasterize pipeline.

## Development plan

The [PythonUltra master list](PYTHONULTRA_ROADMAP.md) is the canonical running
roadmap, cross-referenced against code, tests, commits and hardware reports.
It separates implemented features from active defects and genuinely unbuilt work.

- `main` — primary maintained PythonUltra branch; migration merged through PR #1.
- `migration/independent-cg50` — retained migration history; Run 3 verified its source in CI.
- `cg50-new-display` — preserved prior development branch; historical hardware confirmations apply to their recorded binaries.
- **Completed milestone 1:** compact Pygame compatibility layer and PythonUltra rename.
- **Completed milestone 2:** compact NumPy matrix/vector expansion, including transpose and inverse.
- **Completed milestone 3:** first frozen `py3d` software-rendering engine and rotating-cube demo.
- **Next 3D work:** near-plane triangle clipping, camera/view transforms, mesh loading, frustum culling and performance profiling on physical hardware.
- **Active corrections:** editor layout/input/file safety, ZIP seek/extraction, RC-controlled startup and truthful file metadata.
- **Remaining capabilities:** adjustable date/time with real modification timestamps, standard-library gaps, built-in turtle/matplotl, debugger, PicoC and remaining UI/Files features. The editor, shell and core Files features already exist.

## Collaboration

PythonUltra is maintained in [brandonendall/PythonUltra](https://github.com/brandonendall/PythonUltra). Development history and attribution from [OffCamera-Civilman/PythonExtra-CG50](https://github.com/OffCamera-Civilman/PythonExtra-CG50) are preserved. See the [migration decisions and automation inventory](docs/pythonultra/independent-migration.md).

## Upstream

Original project: **Lephenixnoir/PythonExtra** on Planet Casio.

Source import is complete. The provenance workflow validates the maintained source; future upstream changes are compared and merged on review branches.
