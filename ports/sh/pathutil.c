#include "pathutil.h"

#include <gint/gint.h>
#include <errno.h>
#include <string.h>
#include <sys/stat.h>

static char pe_cwd[PE_PATH_MAX] = "/";

/* gint indirect calls only accept register-sized primitive/pointer arguments.
 * Hide struct stat * behind void * so the world switch follows that ABI. */
static int pe_ws_stat(void *path_in, void *stat_out)
{
    return stat((char const *)path_in, (struct stat *)stat_out);
}

char const *pe_path_getcwd(void)
{
    return pe_cwd;
}

static int pe_append_component(char *out, size_t out_size, size_t *length,
    char const *part, size_t part_len)
{
    size_t need = *length + ((*length > 1) ? 1 : 0) + part_len + 1;
    if(need > out_size) {
        errno = ENAMETOOLONG;
        return -1;
    }
    if(*length > 1)
        out[(*length)++] = '/';
    memcpy(out + *length, part, part_len);
    *length += part_len;
    out[*length] = 0;
    return 0;
}

static void pe_pop_component(char *out, size_t *length)
{
    if(*length <= 1)
        return;
    while(*length > 1 && out[*length - 1] != '/')
        (*length)--;
    if(*length > 1)
        (*length)--;
    out[*length] = 0;
}

static int pe_consume(char const *path, char *out, size_t out_size,
    size_t *length)
{
    char const *p = path;
    while(*p) {
        while(*p == '/') p++;
        if(!*p) break;
        char const *start = p;
        while(*p && *p != '/') p++;
        size_t n = (size_t)(p - start);
        if(n == 1 && start[0] == '.')
            continue;
        if(n == 2 && start[0] == '.' && start[1] == '.') {
            pe_pop_component(out, length);
            continue;
        }
        if(pe_append_component(out, out_size, length, start, n) < 0)
            return -1;
    }
    return 0;
}

int pe_path_resolve(char const *path, char *out, size_t out_size)
{
    if(!path || !out || out_size < 2) {
        errno = EINVAL;
        return -1;
    }

    out[0] = '/';
    out[1] = 0;
    size_t length = 1;

    if(path[0] != '/') {
        if(pe_consume(pe_cwd, out, out_size, &length) < 0)
            return -1;
    }
    if(pe_consume(path, out, out_size, &length) < 0)
        return -1;
    return 0;
}

int pe_path_chdir(char const *path)
{
    char resolved[PE_PATH_MAX];
    struct stat st;
    if(pe_path_resolve(path, resolved, sizeof resolved) < 0)
        return -1;
    if(gint_world_switch(GINT_CALL(pe_ws_stat,
        (void *)resolved, (void *)&st)) < 0)
        return -1;
    if((st.st_mode & S_IFMT) != S_IFDIR) {
        errno = ENOTDIR;
        return -1;
    }
    memcpy(pe_cwd, resolved, strlen(resolved) + 1);
    return 0;
}
