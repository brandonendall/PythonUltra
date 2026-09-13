/* Optional ROM-backed reference for constrained ports. MIT license. */
#ifndef MICROPY_INCLUDED_PY_OBJDOC_H
#define MICROPY_INCLUDED_PY_OBJDOC_H

#include "py/obj.h"

#ifdef MICROPY_PY_DOC_TABLE
mp_obj_t mp_obj_doc_get(mp_obj_t obj);
mp_obj_t mp_obj_doc_unwrap(mp_obj_t obj, mp_obj_t *owner);
mp_obj_t mp_obj_bound_meth_unwrap(mp_obj_t obj, mp_obj_t *owner);
#endif

#endif
