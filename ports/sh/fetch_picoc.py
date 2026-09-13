"""Fetch the pinned PicoC source used by PythonUltra builds.

The vendor tree is generated during the build instead of committing a large
third-party source copy. PicoC is BSD-3-Clause licensed; the upstream LICENSE
is retained inside the generated vendor directory.
"""

from pathlib import Path
import io
import shutil
import tarfile
import urllib.request

COMMIT = "a97d94fa3d4d35c6b78b7de69faac7643e34de22"
URL = "https://codeload.github.com/jpoirier/picoc/tar.gz/" + COMMIT
ROOT = Path(__file__).resolve().parent
DEST = ROOT / "vendor" / "picoc"
MARKER = DEST / ".pythonultra_picoc_commit"

REQUIRED = (
    "LICENSE", "picoc.h", "interpreter.h", "platform.h",
    "table.c", "lex.c", "parse.c", "expression.c", "heap.c", "type.c",
    "variable.c", "clibrary.c", "platform.c", "include.c", "debug.c",
    "cstdlib/stdio.c", "cstdlib/math.c", "cstdlib/string.c",
    "cstdlib/stdlib.c", "cstdlib/time.c", "cstdlib/errno.c",
    "cstdlib/ctype.c", "cstdlib/stdbool.c", "cstdlib/unistd.c",
)


def ready():
    if not MARKER.exists() or MARKER.read_text().strip() != COMMIT:
        return False
    return all((DEST / name).exists() for name in REQUIRED)


def patch_fxcg50_string_library():
    """Replace POSIX-only string helpers with portable ISO-C equivalents."""
    path = DEST / "cstdlib" / "string.c"
    text = path.read_text(encoding="utf-8")

    text = text.replace("= index(Param[0]->Val->Pointer,", "= strchr(Param[0]->Val->Pointer,", 1)
    text = text.replace("= rindex(Param[0]->Val->Pointer,", "= strrchr(Param[0]->Val->Pointer,", 1)

    marker = 'static int String_ZeroValue = 0;\n'
    helpers = r'''static int String_ZeroValue = 0;

#ifdef FXCG50
static char *PythonUltraStrdup(const char *Source)
{
    size_t Length = strlen(Source) + 1;
    char *Copy = malloc(Length);
    if (Copy != NULL)
        memcpy(Copy, Source, Length);
    return Copy;
}

static char *PythonUltraStrtokR(char *String, const char *Delimiters,
    char **SavePtr)
{
    char *Cursor = String != NULL ? String : *SavePtr;
    char *Start;

    if (Cursor == NULL)
        return NULL;

    while (*Cursor != '\0' && strchr(Delimiters, *Cursor) != NULL)
        Cursor++;
    if (*Cursor == '\0') {
        *SavePtr = NULL;
        return NULL;
    }

    Start = Cursor;
    while (*Cursor != '\0' && strchr(Delimiters, *Cursor) == NULL)
        Cursor++;
    if (*Cursor != '\0') {
        *Cursor++ = '\0';
        *SavePtr = Cursor;
    }
    else
        *SavePtr = NULL;

    return Start;
}
#endif
'''
    if marker not in text:
        raise RuntimeError("unexpected PicoC string.c zero-value marker")
    text = text.replace(marker, helpers, 1)
    text = text.replace("(void*)strdup(Param[0]->Val->Pointer)",
                        "(void*)PythonUltraStrdup(Param[0]->Val->Pointer)", 1)
    text = text.replace("(void*)strtok_r(Param[0]->Val->Pointer,",
                        "(void*)PythonUltraStrtokR(Param[0]->Val->Pointer,", 1)
    path.write_text(text, encoding="utf-8")


def patch_fxcg50_time_library():
    """Exclude POSIX-only time helpers unavailable in the fx-CG50 libc."""
    path = DEST / "cstdlib" / "time.c"
    text = path.read_text(encoding="utf-8")
    text = text.replace("#ifndef WIN32\nvoid StdStrptime", "#if !defined(WIN32) && !defined(FXCG50)\nvoid StdStrptime", 1)
    text = text.replace("#ifndef WIN32\n    {StdStrptime", "#if !defined(WIN32) && !defined(FXCG50)\n    {StdStrptime", 1)
    path.write_text(text, encoding="utf-8")


def patch_fxcg50_ctype_library():
    """Replace non-standard ASCII helpers with tiny portable equivalents."""
    path = DEST / "cstdlib" / "ctype.c"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "ReturnValue->Val->Integer = isascii(Param[0]->Val->Integer);",
        "ReturnValue->Val->Integer = ((unsigned int)Param[0]->Val->Integer <= 0x7fU);",
        1,
    )
    text = text.replace(
        "ReturnValue->Val->Integer = toascii(Param[0]->Val->Integer);",
        "ReturnValue->Val->Integer = Param[0]->Val->Integer & 0x7f;",
        1,
    )
    path.write_text(text, encoding="utf-8")


def patch_fxcg50_include_library():
    """Do not register the POSIX unistd library on the calculator."""
    path = DEST / "include.c"
    text = path.read_text(encoding="utf-8")
    old = '# ifndef WIN32\n    IncludeRegister(pc, "unistd.h", &UnistdSetupFunc, &UnistdFunctions[0], UnistdDefs);\n# endif\n'
    new = '# if !defined(WIN32) && !defined(FXCG50)\n    IncludeRegister(pc, "unistd.h", &UnistdSetupFunc, &UnistdFunctions[0], UnistdDefs);\n# endif\n'
    if old not in text:
        raise RuntimeError("unexpected PicoC include.c unistd registration")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main():
    if ready():
        print("PicoC source already pinned at", COMMIT[:12])
        return

    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)

    print("Fetching PicoC", COMMIT[:12])
    with urllib.request.urlopen(URL, timeout=60) as response:
        payload = response.read()

    prefix = "picoc-" + COMMIT + "/"
    wanted = set(REQUIRED)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.startswith(prefix):
                continue
            rel = member.name[len(prefix):]
            if rel not in wanted:
                continue
            target = DEST / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError("missing PicoC archive member " + rel)
            target.write_bytes(source.read())

    missing = [name for name in REQUIRED if not (DEST / name).exists()]
    if missing:
        raise RuntimeError("PicoC archive missing: " + ", ".join(missing))

    platform_h = DEST / "platform.h"
    text = platform_h.read_text(encoding="utf-8")
    old = """#ifdef UNIX_HOST
# include <stdint.h>
# include <unistd.h>
#elif defined(WIN32) /*(predefined on MSVC)*/
#else
# error ***** A platform must be explicitly defined! *****
#endif
"""
    new = """#ifdef UNIX_HOST
# include <stdint.h>
# include <unistd.h>
#elif defined(FXCG50)
/* PythonUltra/fx-CG50: freestanding SH target, no POSIX/readline dependency. */
# include <stdint.h>
#elif defined(WIN32) /*(predefined on MSVC)*/
#else
# error ***** A platform must be explicitly defined! *****
#endif
"""
    if old not in text:
        raise RuntimeError("unexpected PicoC platform.h host-selection block")
    text = text.replace(old, new, 1)
    text = text.replace("#define USE_READLINE\n", "/* PythonUltra: readline disabled */\n", 1)
    platform_h.write_text(text, encoding="utf-8")

    patch_fxcg50_string_library()
    patch_fxcg50_time_library()
    patch_fxcg50_ctype_library()
    patch_fxcg50_include_library()

    MARKER.write_text(COMMIT + "\n", encoding="utf-8")
    print("Prepared PicoC source in", DEST)


if __name__ == "__main__":
    main()
