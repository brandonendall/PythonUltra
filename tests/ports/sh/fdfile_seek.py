"""Run the actual fdfile ioctl logic against host descriptors.

The gint world switch is a counted shim here, not hardware emulation. The
fx-CG50 build and physical round-trip remain separate acceptance gates.
"""

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
source = (ROOT / "ports/sh/fdfile.c").read_text()
start = source.index("typedef struct {\n    int fd;\n    int whence;")
end = source.index("static mp_obj_t fdfile_close", start)
implementation = source[start:end]

prefix = r'''
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
typedef uintptr_t mp_uint_t;
typedef void *mp_obj_t;
typedef struct { int fd; } mp_obj_fdfile_t;
struct mp_stream_seek_t { off_t offset; int whence; };
#define MP_OBJ_TO_PTR(x) (x)
#define MP_STREAM_ERROR ((mp_uint_t)-1)
#define MP_STREAM_SEEK 2
#define MP_STREAM_FLUSH 1
#define MP_EINVAL EINVAL
static int switches;
#define GINT_CALL(fn, ...) fn(__VA_ARGS__)
#define gint_world_switch(call) (++switches, (call))
static void check_fd_is_open(mp_obj_fdfile_t *o) { assert(o->fd >= 0); }
'''

suffix = r'''
int main(void) {
    FILE *stream = tmpfile();
    assert(stream);
    mp_obj_fdfile_t file = { .fd = fileno(stream) };
    assert(write(file.fd, "abcdef", 6) == 6);
    int error = 0;
    struct mp_stream_seek_t seek = { .offset = 0, .whence = SEEK_CUR };
    assert(fdfile_ioctl(&file, MP_STREAM_SEEK, (uintptr_t)&seek, &error) == 0);
    assert(seek.offset == 6);
    seek.offset = 2; seek.whence = SEEK_SET;
    assert(fdfile_ioctl(&file, MP_STREAM_SEEK, (uintptr_t)&seek, &error) == 0);
    char ch = 0;
    assert(read(file.fd, &ch, 1) == 1 && ch == 'c');
    seek.offset = -1; seek.whence = SEEK_END;
    assert(fdfile_ioctl(&file, MP_STREAM_SEEK, (uintptr_t)&seek, &error) == 0);
    assert(seek.offset == 5);
    assert(read(file.fd, &ch, 1) == 1 && ch == 'f');
    seek.offset = -100; seek.whence = SEEK_SET;
    assert(fdfile_ioctl(&file, MP_STREAM_SEEK, (uintptr_t)&seek, &error) == MP_STREAM_ERROR);
    assert(error == EINVAL);
    assert(fdfile_ioctl(&file, MP_STREAM_FLUSH, 0, &error) == 0);
    assert(fdfile_ioctl(&file, 999, 0, &error) == MP_STREAM_ERROR);
    assert(error == EINVAL && switches == 4);
    fclose(stream);
    return 0;
}
'''

with tempfile.TemporaryDirectory(prefix="pythonultra-fdtest-") as folder:
    path = Path(folder)
    (path / "test.c").write_text(prefix + implementation + suffix)
    subprocess.run(["cc", "-Wall", "-Wextra", "-Werror", str(path / "test.c"),
                    "-o", str(path / "test")], check=True)
    subprocess.run([str(path / "test")], check=True)
print("PythonUltra native fdfile seek/tell/error checks passed")
