# Module reference maintenance

`pythonultra_docs.py` builds one plain-text reference per public frozen module
and native module for the fx-CG50 configuration. Run the six serial runtime
preparation scripts first, in an isolated checkout; they modify target source.
The exact sequence is in `.github/workflows/module-documentation.yml`.

Then run:

```sh
python3 tools/pythonultra_docs.py --output build-module-docs/reference --runtime-header ports/sh/module_docs.h
```

The ZIP is written beside `reference/`. Public Python signatures and inherited
methods come from ASTs; native exports and method tables are preprocessed with
the SH port configuration. Native descriptions use checked-in MicroPython docs
with calculator corrections in `pythonultra_doc_content.py`. New public
functions without descriptions fail generation. Update examples and semantic
descriptions whenever behavior changes, even when the signature stays the same.

The reference deliberately documents compatibility no-ops and known defects.
Do not change these to desktop API promises without implementing and verifying
that behavior. The same descriptions now generate `ports/sh/module_docs.h`,
which the fx-CG50 build uses for `help(obj)` and `obj.__doc__`. Generate it after
source preparation and before parallel compilation. It is ignored by git.
Documentation changes trigger both the reference and calculator workflows.

The runtime table is immutable ROM data, resolved against actual module and
member identities. It never imports a module, executes an attribute hook,
replaces a function with a wrapper, or allocates the entire reference in RAM.
Native functions, frozen functions, classes, methods and aliases share the
reference. Documentation lookup does not change the .mpy bytecode format.
This covers bundled public APIs; it does not retain arbitrary user-defined
function docstrings. Existing run131/run132 binaries need a new build for
runtime help, even though their downloadable text reference already exists.

Run `python3 tests/ports/sh/runtime_docs_host.py` in an isolated checkout for
the real MicroPython regression. It builds a dependency-free host interpreter,
checks the requested `py3d.vec3.__doc__` and `help(vec3)`, exercises native and
bound methods, verifies receiver-specific text and checks that help does not
reinitialize gint. Calculator behavior still needs a physical test.

For a local checkout whose commit metadata differs from a verified equivalent
GitHub source tree, `--revision SHA` records that verified upstream identity.
Do not use this option to label different source as an existing release.
