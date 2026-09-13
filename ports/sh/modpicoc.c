//---------------------------------------------------------------------------//
// PythonUltra PicoC bridge: embedded C interpreter for the fx-CG50.
// PicoC upstream is BSD-3-Clause; see vendor/picoc/LICENSE after bootstrap.
//---------------------------------------------------------------------------//

#include "py/runtime.h"
#include "pathutil.h"
#include "vendor/picoc/picoc.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>

/* PicoC's internal stack is a managed arena, not the CPU stack. Start small
   for calculator RAM and make this tunable after hardware profiling. */
#define PYTHONULTRA_PICOC_STACK_SIZE (24 * 1024)

static int pe_picoc_execute_source(const char *name, const char *source,
    size_t source_len, bool call_main)
{
    Picoc *pc = malloc(sizeof(*pc));
    if(pc == NULL)
        mp_raise_msg(&mp_type_MemoryError, MP_ERROR_TEXT("PicoC state"));

    PicocInitialize(pc, PYTHONULTRA_PICOC_STACK_SIZE);
    if(PicocPlatformSetExitPoint(pc)) {
        int result = pc->PicocExitValue;
        PicocCleanup(pc);
        free(pc);
        return result;
    }

    PicocParse(pc, name, source, (int)source_len, true, false, false, false);
    if(call_main)
        PicocCallMain(pc, 0, NULL);

    int result = pc->PicocExitValue;
    PicocCleanup(pc);
    free(pc);
    return result;
}

static mp_obj_t pe_picoc_run(size_t n_args, const mp_obj_t *args)
{
    size_t len = 0;
    const char *source = mp_obj_str_get_data(args[0], &len);
    bool call_main = n_args > 1 ? mp_obj_is_true(args[1]) : false;
    int result = pe_picoc_execute_source("<picoc>", source, len, call_main);
    return MP_OBJ_NEW_SMALL_INT(result);
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(pe_picoc_run_obj, 1, 2, pe_picoc_run);

static mp_obj_t pe_picoc_run_file(size_t n_args, const mp_obj_t *args)
{
    const char *path = mp_obj_str_get_str(args[0]);
    bool call_main = n_args > 1 ? mp_obj_is_true(args[1]) : true;
    char resolved[PE_PATH_MAX];
    if(pe_path_resolve(path, resolved, sizeof resolved) < 0)
        mp_raise_OSError(errno);

    Picoc *pc = malloc(sizeof(*pc));
    if(pc == NULL)
        mp_raise_msg(&mp_type_MemoryError, MP_ERROR_TEXT("PicoC state"));

    PicocInitialize(pc, PYTHONULTRA_PICOC_STACK_SIZE);
    if(PicocPlatformSetExitPoint(pc)) {
        int result = pc->PicocExitValue;
        PicocCleanup(pc);
        free(pc);
        return MP_OBJ_NEW_SMALL_INT(result);
    }

    PicocPlatformScanFile(pc, resolved);
    if(call_main)
        PicocCallMain(pc, 0, NULL);

    int result = pc->PicocExitValue;
    PicocCleanup(pc);
    free(pc);
    return MP_OBJ_NEW_SMALL_INT(result);
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(pe_picoc_run_file_obj, 1, 2,
    pe_picoc_run_file);

static mp_obj_t pe_picoc_version(void)
{
    return mp_obj_new_str(PICOC_VERSION, strlen(PICOC_VERSION));
}
MP_DEFINE_CONST_FUN_OBJ_0(pe_picoc_version_obj, pe_picoc_version);

static const mp_rom_map_elem_t pe_picoc_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_picoc) },
    { MP_ROM_QSTR(MP_QSTR_run), MP_ROM_PTR(&pe_picoc_run_obj) },
    { MP_ROM_QSTR(MP_QSTR_run_file), MP_ROM_PTR(&pe_picoc_run_file_obj) },
    { MP_ROM_QSTR(MP_QSTR_version), MP_ROM_PTR(&pe_picoc_version_obj) },
};
static MP_DEFINE_CONST_DICT(pe_picoc_globals, pe_picoc_globals_table);

const mp_obj_module_t pe_module_picoc = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&pe_picoc_globals,
};

MP_REGISTER_MODULE(MP_QSTR_picoc, pe_module_picoc);
