#ifndef PYTHONULTRA_PATHUTIL_H
#define PYTHONULTRA_PATHUTIL_H

#include <stddef.h>

/* PythonUltra maintains a working directory because the fx-CG50 target libc
   does not provide getcwd()/chdir(). All calculator file APIs can resolve
   relative paths through this layer so terminal cd, os.chdir() and open()
   agree on one current directory. */

#define PE_PATH_MAX 256

char const *pe_path_getcwd(void);
int pe_path_resolve(char const *path, char *out, size_t out_size);
int pe_path_chdir(char const *path);

#endif
