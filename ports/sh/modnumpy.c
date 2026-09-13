//---------------------------------------------------------------------------//
//    ____        PythonExtra                                                //
//.-'`_ o `;__,   A community port of MicroPython for CASIO calculators.     //
//.-'` `---`  '   License: MIT (except some files; see LICENSE)              //
//---------------------------------------------------------------------------//
// pe.modnumpy: compact NumPy-style vector/matrix helpers for game math
//
// This is intentionally not a full ndarray implementation. Functions accept
// Python sequences and return ordinary lists/floats to keep memory use and the
// binary footprint appropriate for calculators.
//---

#include "py/runtime.h"
#include "py/objlist.h"
#include <math.h>

static size_t modnumpy_len(mp_obj_t sequence)
{
    return (size_t)mp_obj_get_int(mp_obj_len(sequence));
}

static mp_obj_t modnumpy_item(mp_obj_t sequence, size_t index)
{
    return mp_obj_subscr(sequence, MP_OBJ_NEW_SMALL_INT(index),
        MP_OBJ_SENTINEL);
}

static mp_float_t modnumpy_number(mp_obj_t sequence, size_t index)
{
    return mp_obj_get_float(modnumpy_item(sequence, index));
}

static mp_obj_t modnumpy_array(mp_obj_t sequence)
{
    size_t length = modnumpy_len(sequence);
    mp_obj_t result = mp_obj_new_list(0, NULL);
    for(size_t i = 0; i < length; i++)
        mp_obj_list_append(result, mp_obj_new_float(modnumpy_number(sequence, i)));
    return result;
}

static mp_obj_t modnumpy_dot(mp_obj_t left, mp_obj_t right)
{
    size_t length = modnumpy_len(left);
    if(modnumpy_len(right) != length)
        mp_raise_ValueError("dot(): vectors must have the same length");

    mp_float_t total = 0;
    for(size_t i = 0; i < length; i++)
        total += modnumpy_number(left, i) * modnumpy_number(right, i);
    return mp_obj_new_float(total);
}

static mp_obj_t modnumpy_cross(mp_obj_t left, mp_obj_t right)
{
    if(modnumpy_len(left) != 3 || modnumpy_len(right) != 3)
        mp_raise_ValueError("cross(): expected two 3D vectors");

    mp_float_t ax = modnumpy_number(left, 0);
    mp_float_t ay = modnumpy_number(left, 1);
    mp_float_t az = modnumpy_number(left, 2);
    mp_float_t bx = modnumpy_number(right, 0);
    mp_float_t by = modnumpy_number(right, 1);
    mp_float_t bz = modnumpy_number(right, 2);

    mp_obj_t result = mp_obj_new_list(0, NULL);
    mp_obj_list_append(result, mp_obj_new_float(ay * bz - az * by));
    mp_obj_list_append(result, mp_obj_new_float(az * bx - ax * bz));
    mp_obj_list_append(result, mp_obj_new_float(ax * by - ay * bx));
    return result;
}

static mp_obj_t modnumpy_norm(mp_obj_t vector)
{
    size_t length = modnumpy_len(vector);
    mp_float_t squared = 0;
    for(size_t i = 0; i < length; i++) {
        mp_float_t value = modnumpy_number(vector, i);
        squared += value * value;
    }
    return mp_obj_new_float(sqrt(squared));
}

static mp_obj_t modnumpy_normalize(mp_obj_t vector)
{
    size_t length = modnumpy_len(vector);
    mp_float_t squared = 0;
    for(size_t i = 0; i < length; i++) {
        mp_float_t value = modnumpy_number(vector, i);
        squared += value * value;
    }

    mp_float_t magnitude = sqrt(squared);
    if(magnitude == 0)
        mp_raise_ValueError("normalize(): zero-length vector");

    mp_obj_t result = mp_obj_new_list(0, NULL);
    for(size_t i = 0; i < length; i++)
        mp_obj_list_append(result,
            mp_obj_new_float(modnumpy_number(vector, i) / magnitude));
    return result;
}

static mp_obj_t modnumpy_lerp(mp_obj_t start, mp_obj_t end, mp_obj_t amount)
{
    size_t length = modnumpy_len(start);
    if(modnumpy_len(end) != length)
        mp_raise_ValueError("lerp(): vectors must have the same length");

    mp_float_t t = mp_obj_get_float(amount);
    mp_obj_t result = mp_obj_new_list(0, NULL);
    for(size_t i = 0; i < length; i++) {
        mp_float_t a = modnumpy_number(start, i);
        mp_float_t b = modnumpy_number(end, i);
        mp_obj_list_append(result, mp_obj_new_float(a + (b - a) * t));
    }
    return result;
}

static mp_obj_t modnumpy_matmul(mp_obj_t left, mp_obj_t right)
{
    size_t left_rows = modnumpy_len(left);
    size_t right_rows = modnumpy_len(right);
    if(left_rows == 0 || right_rows == 0)
        return mp_obj_new_list(0, NULL);

    size_t inner = modnumpy_len(modnumpy_item(left, 0));
    size_t columns = modnumpy_len(modnumpy_item(right, 0));
    if(inner != right_rows)
        mp_raise_ValueError("matmul(): incompatible matrix dimensions");

    for(size_t row = 0; row < left_rows; row++) {
        if(modnumpy_len(modnumpy_item(left, row)) != inner)
            mp_raise_ValueError("matmul(): ragged left matrix");
    }
    for(size_t row = 0; row < right_rows; row++) {
        if(modnumpy_len(modnumpy_item(right, row)) != columns)
            mp_raise_ValueError("matmul(): ragged right matrix");
    }

    mp_obj_t result = mp_obj_new_list(0, NULL);
    for(size_t row = 0; row < left_rows; row++) {
        mp_obj_t output_row = mp_obj_new_list(0, NULL);
        mp_obj_t left_row = modnumpy_item(left, row);
        for(size_t column = 0; column < columns; column++) {
            mp_float_t total = 0;
            for(size_t k = 0; k < inner; k++) {
                mp_obj_t right_row = modnumpy_item(right, k);
                total += modnumpy_number(left_row, k)
                    * modnumpy_number(right_row, column);
            }
            mp_obj_list_append(output_row, mp_obj_new_float(total));
        }
        mp_obj_list_append(result, output_row);
    }
    return result;
}

MP_DEFINE_CONST_FUN_OBJ_1(modnumpy_array_obj, modnumpy_array);
MP_DEFINE_CONST_FUN_OBJ_2(modnumpy_dot_obj, modnumpy_dot);
MP_DEFINE_CONST_FUN_OBJ_2(modnumpy_cross_obj, modnumpy_cross);
MP_DEFINE_CONST_FUN_OBJ_1(modnumpy_norm_obj, modnumpy_norm);
MP_DEFINE_CONST_FUN_OBJ_1(modnumpy_normalize_obj, modnumpy_normalize);
MP_DEFINE_CONST_FUN_OBJ_3(modnumpy_lerp_obj, modnumpy_lerp);
MP_DEFINE_CONST_FUN_OBJ_2(modnumpy_matmul_obj, modnumpy_matmul);

static const mp_rom_map_elem_t modnumpy_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_numpy) },
    { MP_ROM_QSTR(MP_QSTR_array), MP_ROM_PTR(&modnumpy_array_obj) },
    { MP_ROM_QSTR(MP_QSTR_dot), MP_ROM_PTR(&modnumpy_dot_obj) },
    { MP_ROM_QSTR(MP_QSTR_cross), MP_ROM_PTR(&modnumpy_cross_obj) },
    { MP_ROM_QSTR(MP_QSTR_norm), MP_ROM_PTR(&modnumpy_norm_obj) },
    { MP_ROM_QSTR(MP_QSTR_normalize), MP_ROM_PTR(&modnumpy_normalize_obj) },
    { MP_ROM_QSTR(MP_QSTR_lerp), MP_ROM_PTR(&modnumpy_lerp_obj) },
    { MP_ROM_QSTR(MP_QSTR_matmul), MP_ROM_PTR(&modnumpy_matmul_obj) },
};
static MP_DEFINE_CONST_DICT(
    modnumpy_module_globals, modnumpy_module_globals_table);

const mp_obj_module_t modnumpy_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&modnumpy_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_numpy, modnumpy_module);
