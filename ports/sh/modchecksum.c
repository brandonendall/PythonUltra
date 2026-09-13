//---------------------------------------------------------------------------//
//    ____        PythonUltra                                                //
//.-'`_ o `;__,   A community port of MicroPython for CASIO calculators.     //
//.-'` `---`  '   License: MIT (except some files; see LICENSE)              //
//---------------------------------------------------------------------------//
// pe.modchecksum: small streaming file checksums for the fx-CG50.

#include "py/runtime.h"
#include "pathutil.h"

#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <gint/gint.h>

#include "lib/crypto-algorithms/sha256.h"
#include "lib/crypto-algorithms/sha1.h"

/* Compile the compact dependency-free digest backends into this one module.
   hashlib is not enabled in this port, so there are no duplicate symbols. */
#include "lib/crypto-algorithms/sha256.c"
#include "lib/crypto-algorithms/sha1.c"

#define PE_CHECKSUM_BUFSIZE 512

static int pe_checksum_ws_open(void *path_in)
{
    return open((char const *)path_in, O_RDONLY);
}

static int pe_checksum_ws_read(int fd, void *buffer, int size)
{
    return (int)read(fd, buffer, (size_t)size);
}

static int pe_checksum_ws_close(int fd)
{
    return close(fd);
}

static int pe_checksum_open(mp_obj_t path_in)
{
    char resolved[PE_PATH_MAX];
    char const *path = mp_obj_str_get_str(path_in);
    if(pe_path_resolve(path, resolved, sizeof resolved) < 0)
        mp_raise_OSError(errno);

    int fd = gint_world_switch(GINT_CALL(pe_checksum_ws_open,
        (void *)resolved));
    if(fd < 0)
        mp_raise_OSError(errno);
    return fd;
}

static void pe_checksum_close(int fd)
{
    if(gint_world_switch(GINT_CALL(pe_checksum_ws_close, fd)) < 0)
        mp_raise_OSError(errno);
}

static int pe_checksum_read(int fd, void *buffer, int size)
{
    int result = gint_world_switch(GINT_CALL(pe_checksum_ws_read,
        fd, buffer, size));
    if(result < 0)
        mp_raise_OSError(errno);
    return result;
}

static mp_obj_t pe_checksum_hex(uint8_t const *digest, size_t size)
{
    static char const hex[] = "0123456789abcdef";
    char out[SHA256_BLOCK_SIZE * 2 + 1];
    for(size_t i = 0; i < size; i++) {
        out[i * 2] = hex[digest[i] >> 4];
        out[i * 2 + 1] = hex[digest[i] & 0x0f];
    }
    out[size * 2] = 0;
    return mp_obj_new_str(out, size * 2);
}

static mp_obj_t pe_checksum_sha256_file(mp_obj_t path_in)
{
    int fd = pe_checksum_open(path_in);
    CRYAL_SHA256_CTX ctx;
    uint8_t buffer[PE_CHECKSUM_BUFSIZE];
    uint8_t digest[SHA256_BLOCK_SIZE];
    sha256_init(&ctx);

    while(1) {
        int count = pe_checksum_read(fd, buffer, sizeof buffer);
        if(count == 0)
            break;
        sha256_update(&ctx, buffer, (size_t)count);
        MICROPY_VM_HOOK_LOOP;
    }
    pe_checksum_close(fd);
    sha256_final(&ctx, digest);
    return pe_checksum_hex(digest, sizeof digest);
}
MP_DEFINE_CONST_FUN_OBJ_1(pe_checksum_sha256_file_obj,
    pe_checksum_sha256_file);

static mp_obj_t pe_checksum_sha1_file(mp_obj_t path_in)
{
    int fd = pe_checksum_open(path_in);
    CRYAL_SHA1_CTX ctx;
    uint8_t buffer[PE_CHECKSUM_BUFSIZE];
    uint8_t digest[SHA1_BLOCK_SIZE];
    sha1_init(&ctx);

    while(1) {
        int count = pe_checksum_read(fd, buffer, sizeof buffer);
        if(count == 0)
            break;
        sha1_update(&ctx, buffer, (size_t)count);
        MICROPY_VM_HOOK_LOOP;
    }
    pe_checksum_close(fd);
    sha1_final(&ctx, digest);
    return pe_checksum_hex(digest, sizeof digest);
}
MP_DEFINE_CONST_FUN_OBJ_1(pe_checksum_sha1_file_obj,
    pe_checksum_sha1_file);

static const mp_rom_map_elem_t pe_checksum_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_checksum) },
    { MP_ROM_QSTR(MP_QSTR_sha256_file),
        MP_ROM_PTR(&pe_checksum_sha256_file_obj) },
    { MP_ROM_QSTR(MP_QSTR_sha1_file),
        MP_ROM_PTR(&pe_checksum_sha1_file_obj) },
};
static MP_DEFINE_CONST_DICT(pe_checksum_globals, pe_checksum_globals_table);

const mp_obj_module_t pe_module_checksum = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&pe_checksum_globals,
};

MP_REGISTER_MODULE(MP_QSTR_checksum, pe_module_checksum);
