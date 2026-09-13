/* Dependency-free Unix interpreter exercising the same ROM doc lookup. */
#include "ports/unix/variants/minimal/mpconfigvariant.h"
#undef MICROPY_CONFIG_ROM_LEVEL
#define MICROPY_CONFIG_ROM_LEVEL MICROPY_CONFIG_ROM_LEVEL_CORE_FEATURES
#define MICROPY_PY_DOC_TABLE "ports/sh/module_docs.h"
#define MICROPY_PY_BUILTINS_HELP (1)
#define MICROPY_PY_BUILTINS_HELP_MODULES (1)
#define MICROPY_PY_BUILTINS_PROPERTY (1)
#define MICROPY_PY_ALL_SPECIAL_METHODS (1)
#define MICROPY_BUILTIN_METHOD_CHECK_SELF_ARG (1)
#define MICROPY_FLOAT_IMPL MICROPY_FLOAT_IMPL_DOUBLE
#define MICROPY_PY_MATH (1)
#define MICROPY_PY_TIME (1)
#define MICROPY_PY_IO (1)
#define MICROPY_PY_IO_FILEIO (1)
#define MICROPY_PY_SYS_MODULES (1)
