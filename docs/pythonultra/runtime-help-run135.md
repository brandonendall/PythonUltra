# Runtime module help: run #135

- Source: `f718931c7836722a3f20f086de9b70cc5ad2f218`, `cg50-new-display`.
- [Successful calculator build](https://github.com/OffCamera-Civilman/PythonExtra-CG50/actions/runs/34718875834).
- [Download the build artifact](https://github.com/OffCamera-Civilman/PythonExtra-CG50/actions/runs/34718875834/artifacts/10305523412).
- Add-in: `PythonUltra-CG50-run135.g3a`, **630,404 bytes**, below the 2 MB target.
- Artifact archive: 745,966 bytes; SHA-256
  `70d55d95ac90b8455a34ae56f00810f0bcb507dd83b6afae564e724cf1182cf5`.
  The add-in's own SHA-256 is supplied in the artifact's `SHA256SUMS.txt`.
- CI reference ZIP SHA-256:
  `fe60bb3dc674ecbcc7f6d3df26bfdc1ab719f27533e48e9b5c60e0f37af9c3a8`.

## Runtime behavior

The source-audited descriptions used for the text reference now also back
`help(obj)` and `obj.__doc__` for bundled public native/frozen functions,
classes and methods. The table and string objects are const ROM data. Lookup
uses actual objects and reads module/class dictionaries without importing
modules or executing attribute hooks. Calling a documented function still
uses its original implementation and calling convention; the .mpy format is
unchanged.

Module help includes purpose, calculator limits, an example and member
signatures. Function help includes the supported signature and description.
The host MicroPython regression exercises py3d, native math/builtin methods,
Pygame classes, bound and inherited methods, aliases, shared native method
tables, immutable-string hashing and unrelated same-named functions.

This covers the bundled public API. It does not retain arbitrary user-defined
function docstrings. Run131/run132 binaries have the offline reference but
need the new add-in for this runtime help.

## Documentation download and maintenance

[Plain-text module reference ZIP](PythonUltra-Module-Documentation-run135.zip)
contains 43 module/submodule references, 1,283 inventoried members, aliases and
constants, examples, a module index and the MicroPython license. No public
descriptions are missing. This repository copy was generated from the verified
run135 source tree; ZIP timestamps make its archive hash differ from the CI
archive. Its SHA-256 is
`024b4e491972c36e28ba68933fc52314ed6e793fc725df9b1c00d37d5923f18c`.

`tools/pythonultra_docs.py` regenerates the reference and ROM table from the
prepared source. Missing member descriptions fail generation. Both relevant
workflows run automatically on API/reference changes; the calculator workflow
uploads a fresh matching ZIP with each build. This named repository archive is
the run135 snapshot, not a claim to describe later releases.

## Calculator acceptance

Install the new add-in and try:

```python
from py3d import vec3
help(vec3)
print(vec3.__doc__)
import math
help(math.sqrt)
import pygame
help(pygame.Surface.set_colorkey)
```

Confirm the text is readable and scrollable, then run the corrected
`colorkey_motion.py` to confirm display behavior after using help. The compiler,
host regressions and G3A size/API checks pass; physical-calculator confirmation
of this new help remains open. The user's separate run131 color-key success is
recorded in [its receipt](colorkey-run131.md), and does not close the editor,
dark-mode or clock/timestamp tasks.

Runs133/134 passed the runtime-help tests but stopped when source preparation
was inadvertently repeated. Run135 prepares once, tests that prepared source,
and compiles it successfully.
