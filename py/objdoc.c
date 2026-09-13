/* ROM-backed module documentation. MIT license; see LICENSE.
 * Never imports a module or calls user attribute hooks: on the calculator,
 * importing gint can clear the display. No wrappers or per-call overhead.
 */
#include "py/runtime.h"
#include "py/objdoc.h"

#ifdef MICROPY_PY_DOC_TABLE
#include "py/objmodule.h"
#include "py/objstr.h"
#include "py/objtuple.h"
#include "py/objtype.h"

typedef struct {
    qstr module;
    qstr path[4];
    const mp_obj_str_t *text;
} mp_doc_entry_t;

#include MICROPY_PY_DOC_TABLE

static mp_obj_t doc_map(const mp_map_t *map, qstr key) {
    mp_map_elem_t *entry = mp_map_lookup((mp_map_t *)map,
        MP_OBJ_NEW_QSTR(key), MP_MAP_LOOKUP);
    return entry ? entry->value : MP_OBJ_NULL;
}

static mp_obj_t doc_type(const mp_obj_type_t *type, qstr key, unsigned depth) {
    if (depth == 16) {
        return MP_OBJ_NULL;
    }
    if (MP_OBJ_TYPE_HAS_SLOT(type, locals_dict)) {
        mp_obj_t value = doc_map(&MP_OBJ_TYPE_GET_SLOT(type, locals_dict)->map, key);
        if (value != MP_OBJ_NULL) {
            return value;
        }
    }
    if (MP_OBJ_TYPE_HAS_SLOT(type, parent)) {
        mp_obj_t parent = MP_OBJ_FROM_PTR(MP_OBJ_TYPE_GET_SLOT(type, parent));
        if (mp_obj_is_type(parent, &mp_type_tuple)) {
            const mp_obj_tuple_t *parents = MP_OBJ_TO_PTR(parent);
            for (size_t i = 0; i < parents->len; ++i) {
                mp_obj_t value = doc_type(MP_OBJ_TO_PTR(parents->items[i]), key, depth + 1);
                if (value != MP_OBJ_NULL) {
                    return value;
                }
            }
        } else {
            return doc_type(MP_OBJ_TO_PTR(parent), key, depth + 1);
        }
    }
    return MP_OBJ_NULL;
}

static mp_obj_t doc_member(mp_obj_t obj, qstr key) {
    if (mp_obj_is_type(obj, &mp_type_module)) {
        return doc_map(&mp_obj_module_get_globals(obj)->map, key);
    }
    if (mp_obj_is_type(obj, &mp_type_type)) {
        return doc_type(MP_OBJ_TO_PTR(obj), key, 0);
    }
    const mp_obj_type_t *type = mp_obj_get_type(obj);
    if (mp_obj_is_instance_type(type)) {
        mp_obj_instance_t *instance = MP_OBJ_TO_PTR(obj);
        mp_obj_t value = doc_map(&instance->members, key);
        if (value != MP_OBJ_NULL) {
            return value;
        }
    }
    return doc_type(type, key, 0);
}

static mp_obj_t doc_module(qstr name) {
    mp_obj_t obj = doc_map(&MP_STATE_VM(mp_loaded_modules_dict).map, name);
    if (obj == MP_OBJ_NULL) {
        obj = doc_map(&mp_builtin_module_map, name);
    }
    if (obj == MP_OBJ_NULL) {
        obj = doc_map(&mp_builtin_extensible_module_map, name);
    }
    return obj;
}

mp_obj_t mp_obj_doc_get(mp_obj_t obj) {
    mp_obj_t owner = MP_OBJ_NULL;
    obj = mp_obj_doc_unwrap(obj, &owner);
    if (!mp_obj_is_obj(obj)) {
        return MP_OBJ_NULL;
    }
    const mp_obj_type_t *type = mp_obj_get_type(obj);
    if (type != &mp_type_module && type != &mp_type_type
        && !mp_obj_is_instance_type(type) && !MP_OBJ_TYPE_HAS_SLOT(type, call)) {
        return MP_OBJ_NULL;
    }
    qstr previous = MP_QSTRnull;
    mp_obj_t module = MP_OBJ_NULL;
    for (size_t i = 0; i < MP_ARRAY_SIZE(mp_doc_entries); ++i) {
        const mp_doc_entry_t *entry = &mp_doc_entries[i];
        if (entry->module != previous) {
            module = doc_module(entry->module);
            previous = entry->module;
        }
        mp_obj_t value = module, parent = MP_OBJ_NULL;
        for (size_t j = 0; j < MP_ARRAY_SIZE(entry->path)
            && entry->path[j] != MP_QSTRnull && value != MP_OBJ_NULL; ++j) {
            parent = value;
            value = doc_member(value, entry->path[j]);
        }
        if (value == MP_OBJ_NULL) {
            continue;
        }
        mp_obj_t ignored = MP_OBJ_NULL;
        value = mp_obj_doc_unwrap(value, &ignored);
        if (value != obj) {
            continue;
        }
        // Shared native method tables (eg str/bytes, BytesIO/StringIO) need
        // the receiver's class as well as the function's identity.
        if (owner != MP_OBJ_NULL && parent != MP_OBJ_NULL
            && mp_obj_is_type(parent, &mp_type_type)) {
            mp_obj_t owner_type = mp_obj_is_type(owner, &mp_type_type)
                ? owner : MP_OBJ_FROM_PTR(mp_obj_get_type(owner));
            if (!mp_obj_is_subclass_fast(owner_type, parent)) {
                continue;
            }
        }
        return MP_OBJ_FROM_PTR(entry->text);
    }
    return MP_OBJ_NULL;
}
#endif
