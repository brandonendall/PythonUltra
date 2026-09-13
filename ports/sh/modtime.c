//---------------------------------------------------------------------------//
//    ____        PythonExtra                                                //
//.-'`_ o `;__,   A community port of MicroPython for CASIO calculators.     //
//.-'` `---`  '   License: MIT (except some files; see LICENSE)              //
//---------------------------------------------------------------------------//
// pe.modtime: Custom extensions to the `time` module

#include <time.h>
#include "py/runtime.h"
#include "py/objint.h"
#include "wallclock.h"

static mp_obj_t time_monotonic(void) {
    return mp_obj_new_float((mp_float_t)pe_monotonic_ms() / 1000);
}
MP_DEFINE_CONST_FUN_OBJ_0(mp_time_monotonic_obj, time_monotonic);

static mp_obj_t mp_time_time_get(void) {
    uint32_t seconds;
    if(!pe_clock_read(&seconds))
        mp_raise_ValueError(MP_ERROR_TEXT("RTC date invalid; set Date/Time"));
    return mp_obj_new_int_from_uint(seconds);
}

static mp_obj_t pe_time_localtime(size_t n_args, mp_obj_t const *args)
{
    uint32_t seconds;
    int fields[8];
    if(n_args == 0 || args[0] == mp_const_none) {
        if(!pe_clock_read(&seconds))
            mp_raise_ValueError(MP_ERROR_TEXT("RTC date invalid; set Date/Time"));
    }
    else {
        if(!mp_obj_is_int(args[0]))
            mp_raise_TypeError(MP_ERROR_TEXT("seconds must be an integer"));
        /* Unsigned conversion also handles 2038..2099 on the 32-bit target. */
        seconds = mp_obj_int_get_uint_checked(args[0]);
    }
    if(!pe_clock_decode(seconds, fields))
        mp_raise_ValueError(MP_ERROR_TEXT("date outside 1970..2099"));
    mp_obj_t tuple[8];
    for(int i = 0; i < 8; i++)
        tuple[i] = mp_obj_new_int(fields[i]);
    return mp_obj_new_tuple(8, tuple);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(pe_time_localtime_obj, 0, 1, pe_time_localtime);

static void pe_time_fields(mp_obj_t value, int fields[6], bool setting)
{
    size_t len;
    mp_obj_t *items;
    mp_obj_get_array(value, &len, &items);
    if((setting && len != 6 && len != 8 && len != 9)
            || (!setting && len != 8 && len != 9))
        mp_raise_TypeError(MP_ERROR_TEXT("expected date/time tuple"));
    for(int i = 0; i < 6; i++)
        fields[i] = mp_obj_get_int(items[i]);
    if(!pe_clock_valid(fields))
        mp_raise_ValueError(MP_ERROR_TEXT("invalid date/time (1970..2099)"));
}

static mp_obj_t pe_time_mktime(mp_obj_t value)
{
    int fields[6];
    pe_time_fields(value, fields, false);
    return mp_obj_new_int_from_uint(pe_clock_encode(fields));
}
static MP_DEFINE_CONST_FUN_OBJ_1(pe_time_mktime_obj, pe_time_mktime);

static mp_obj_t pe_time_set_datetime(mp_obj_t value)
{
    int fields[6];
    pe_time_fields(value, fields, true);
    pe_clock_set(fields);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(pe_time_set_datetime_obj, pe_time_set_datetime);

#define MICROPY_PY_TIME_EXTRA_GLOBALS \
    { MP_ROM_QSTR(MP_QSTR_monotonic), MP_ROM_PTR(&mp_time_monotonic_obj) }, \
    { MP_ROM_QSTR(MP_QSTR_localtime), MP_ROM_PTR(&pe_time_localtime_obj) }, \
    { MP_ROM_QSTR(MP_QSTR_gmtime), MP_ROM_PTR(&pe_time_localtime_obj) }, \
    { MP_ROM_QSTR(MP_QSTR_mktime), MP_ROM_PTR(&pe_time_mktime_obj) }, \
    { MP_ROM_QSTR(MP_QSTR_set_datetime), MP_ROM_PTR(&pe_time_set_datetime_obj) },
