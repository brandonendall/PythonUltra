//---------------------------------------------------------------------------//
//    ____        PythonExtra                                                //
//.-'`_ o `;__,   A community port of MicroPython for CASIO calculators.     //
//.-'` `---`  '   License: MIT (except some files; see LICENSE)              //
//---------------------------------------------------------------------------//
// pe.modctypes: restricted ctypes-style native interface
//
// This module deliberately has no dlsym(), arbitrary address constructor, or
// unrestricted memory access. Native calls are allowlisted and pointer-like
// operations are confined to bounds-checked Python buffer objects.
//---

#include "py/runtime.h"
#include "py/objarray.h"
#include <math.h>
#include <stdint.h>
#include <string.h>

static mp_obj_t modctypes_c_int(mp_obj_t value)
{
    return mp_obj_new_int(mp_obj_get_int(value));
}

static mp_obj_t modctypes_c_uint(mp_obj_t value)
{
    mp_int_t number = mp_obj_get_int(value);
    if(number < 0)
        mp_raise_ValueError("c_uint(): value must be non-negative");
    return mp_obj_new_int_from_uint((mp_uint_t)number);
}

static mp_obj_t modctypes_c_float(mp_obj_t value)
{
    return mp_obj_new_float(mp_obj_get_float(value));
}

static mp_obj_t modctypes_c_bool(mp_obj_t value)
{
    return mp_obj_new_bool(mp_obj_is_true(value));
}

static size_t modctypes_index(mp_obj_t value, size_t length)
{
    mp_int_t index = mp_obj_get_int(value);
    if(index < 0 || (size_t)index >= length)
        mp_raise_ValueError("buffer index out of range");
    return (size_t)index;
}

static size_t modctypes_count(mp_obj_t value)
{
    mp_int_t count = mp_obj_get_int(value);
    if(count < 0)
        mp_raise_ValueError("count must be non-negative");
    return (size_t)count;
}

static mp_obj_t modctypes_read_u8(mp_obj_t object, mp_obj_t offset)
{
    mp_buffer_info_t buffer;
    mp_get_buffer_raise(object, &buffer, MP_BUFFER_READ);
    size_t index = modctypes_index(offset, buffer.len);
    return MP_OBJ_NEW_SMALL_INT(((uint8_t *)buffer.buf)[index]);
}

static mp_obj_t modctypes_write_u8(
    mp_obj_t object, mp_obj_t offset, mp_obj_t value)
{
    mp_buffer_info_t buffer;
    mp_get_buffer_raise(object, &buffer, MP_BUFFER_WRITE);
    size_t index = modctypes_index(offset, buffer.len);
    mp_int_t number = mp_obj_get_int(value);
    if(number < 0 || number > 255)
        mp_raise_ValueError("write_u8(): value must be between 0 and 255");
    ((uint8_t *)buffer.buf)[index] = (uint8_t)number;
    return mp_const_none;
}

static mp_obj_t modctypes_fill(mp_obj_t object, mp_obj_t value)
{
    mp_buffer_info_t buffer;
    mp_get_buffer_raise(object, &buffer, MP_BUFFER_WRITE);
    mp_int_t number = mp_obj_get_int(value);
    if(number < 0 || number > 255)
        mp_raise_ValueError("fill(): value must be between 0 and 255");
    memset(buffer.buf, number, buffer.len);
    return object;
}

static mp_obj_t modctypes_copy(size_t n_args, mp_obj_t const *args)
{
    mp_buffer_info_t destination;
    mp_buffer_info_t source;
    mp_get_buffer_raise(args[0], &destination, MP_BUFFER_WRITE);
    mp_get_buffer_raise(args[2], &source, MP_BUFFER_READ);

    mp_int_t destination_offset_i = mp_obj_get_int(args[1]);
    mp_int_t source_offset_i = mp_obj_get_int(args[3]);
    size_t count = modctypes_count(args[4]);
    if(destination_offset_i < 0 || source_offset_i < 0)
        mp_raise_ValueError("copy(): offsets must be non-negative");

    size_t destination_offset = (size_t)destination_offset_i;
    size_t source_offset = (size_t)source_offset_i;
    if(destination_offset > destination.len
        || count > destination.len - destination_offset
        || source_offset > source.len
        || count > source.len - source_offset)
        mp_raise_ValueError("copy(): range exceeds buffer");

    memmove((uint8_t *)destination.buf + destination_offset,
        (uint8_t *)source.buf + source_offset, count);
    return args[0];
}

static mp_obj_t modctypes_available(void)
{
    mp_obj_t functions[] = {
        mp_obj_new_str("abs", 3),
        mp_obj_new_str("sqrt", 4),
        mp_obj_new_str("sin", 3),
        mp_obj_new_str("cos", 3),
        mp_obj_new_str("pow", 3),
        mp_obj_new_str("clamp", 5),
    };
    return mp_obj_new_tuple(
        sizeof functions / sizeof functions[0], functions);
}

static void modctypes_require_arity(
    char const *name, size_t actual, size_t expected)
{
    (void)name;
    if(actual != expected)
        mp_raise_TypeError("wrong number of native-call arguments");
}

static mp_obj_t modctypes_call(size_t n_args, mp_obj_t const *args)
{
    char const *name = mp_obj_str_get_str(args[0]);
    size_t count = n_args - 1;

    if(!strcmp(name, "abs")) {
        modctypes_require_arity(name, count, 1);
        mp_int_t value = mp_obj_get_int(args[1]);
        if(value < 0)
            value = -value;
        return mp_obj_new_int(value);
    }
    if(!strcmp(name, "sqrt")) {
        modctypes_require_arity(name, count, 1);
        return mp_obj_new_float(sqrt(mp_obj_get_float(args[1])));
    }
    if(!strcmp(name, "sin")) {
        modctypes_require_arity(name, count, 1);
        return mp_obj_new_float(sin(mp_obj_get_float(args[1])));
    }
    if(!strcmp(name, "cos")) {
        modctypes_require_arity(name, count, 1);
        return mp_obj_new_float(cos(mp_obj_get_float(args[1])));
    }
    if(!strcmp(name, "pow")) {
        modctypes_require_arity(name, count, 2);
        return mp_obj_new_float(pow(
            mp_obj_get_float(args[1]), mp_obj_get_float(args[2])));
    }
    if(!strcmp(name, "clamp")) {
        modctypes_require_arity(name, count, 3);
        mp_int_t value = mp_obj_get_int(args[1]);
        mp_int_t lower = mp_obj_get_int(args[2]);
        mp_int_t upper = mp_obj_get_int(args[3]);
        if(lower > upper)
            mp_raise_ValueError("clamp(): lower bound exceeds upper bound");
        if(value < lower) value = lower;
        if(value > upper) value = upper;
        return mp_obj_new_int(value);
    }

    mp_raise_ValueError("native function is not allowlisted");
}

MP_DEFINE_CONST_FUN_OBJ_1(modctypes_c_int_obj, modctypes_c_int);
MP_DEFINE_CONST_FUN_OBJ_1(modctypes_c_uint_obj, modctypes_c_uint);
MP_DEFINE_CONST_FUN_OBJ_1(modctypes_c_float_obj, modctypes_c_float);
MP_DEFINE_CONST_FUN_OBJ_1(modctypes_c_double_obj, modctypes_c_float);
MP_DEFINE_CONST_FUN_OBJ_1(modctypes_c_bool_obj, modctypes_c_bool);
MP_DEFINE_CONST_FUN_OBJ_2(modctypes_read_u8_obj, modctypes_read_u8);
MP_DEFINE_CONST_FUN_OBJ_3(modctypes_write_u8_obj, modctypes_write_u8);
MP_DEFINE_CONST_FUN_OBJ_2(modctypes_fill_obj, modctypes_fill);
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    modctypes_copy_obj, 5, 5, modctypes_copy);
MP_DEFINE_CONST_FUN_OBJ_0(modctypes_available_obj, modctypes_available);
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    modctypes_call_obj, 1, 4, modctypes_call);

static const mp_rom_map_elem_t modctypes_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ctypes) },
    { MP_ROM_QSTR(MP_QSTR_c_int), MP_ROM_PTR(&modctypes_c_int_obj) },
    { MP_ROM_QSTR(MP_QSTR_c_uint), MP_ROM_PTR(&modctypes_c_uint_obj) },
    { MP_ROM_QSTR(MP_QSTR_c_float), MP_ROM_PTR(&modctypes_c_float_obj) },
    { MP_ROM_QSTR(MP_QSTR_c_double), MP_ROM_PTR(&modctypes_c_double_obj) },
    { MP_ROM_QSTR(MP_QSTR_c_bool), MP_ROM_PTR(&modctypes_c_bool_obj) },
    { MP_ROM_QSTR(MP_QSTR_buffer), MP_ROM_PTR(&mp_type_bytearray) },
    { MP_ROM_QSTR(MP_QSTR_read_u8), MP_ROM_PTR(&modctypes_read_u8_obj) },
    { MP_ROM_QSTR(MP_QSTR_write_u8), MP_ROM_PTR(&modctypes_write_u8_obj) },
    { MP_ROM_QSTR(MP_QSTR_fill), MP_ROM_PTR(&modctypes_fill_obj) },
    { MP_ROM_QSTR(MP_QSTR_copy), MP_ROM_PTR(&modctypes_copy_obj) },
    { MP_ROM_QSTR(MP_QSTR_available), MP_ROM_PTR(&modctypes_available_obj) },
    { MP_ROM_QSTR(MP_QSTR_call), MP_ROM_PTR(&modctypes_call_obj) },
    { MP_ROM_QSTR(MP_QSTR_SAFE), MP_ROM_TRUE },
};
static MP_DEFINE_CONST_DICT(
    modctypes_module_globals, modctypes_module_globals_table);

const mp_obj_module_t modctypes_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&modctypes_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_ctypes, modctypes_module);
