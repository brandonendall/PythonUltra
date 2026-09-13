/* Small libc functions missing from the fx-CG50 target runtime. */

#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

int strncmp(const char *lhs, const char *rhs, size_t count)
{
    const unsigned char *left = (const unsigned char *)lhs;
    const unsigned char *right = (const unsigned char *)rhs;

    while(count-- > 0) {
        unsigned char a = *left++;
        unsigned char b = *right++;

        if(a != b)
            return (int)a - (int)b;
        if(a == '\0')
            return 0;
    }

    return 0;
}

char *strncat(char *dst, const char *src, size_t count)
{
    char *out = dst;
    while(*dst != '\0')
        dst++;
    while(count-- > 0 && *src != '\0')
        *dst++ = *src++;
    *dst = '\0';
    return out;
}

char *strpbrk(const char *text, const char *accept)
{
    const char *p;
    for(; *text != '\0'; text++) {
        for(p = accept; *p != '\0'; p++) {
            if(*text == *p)
                return (char *)text;
        }
    }
    return NULL;
}

char *strstr(const char *haystack, const char *needle)
{
    const char *h;
    const char *n;

    if(*needle == '\0')
        return (char *)haystack;

    for(; *haystack != '\0'; haystack++) {
        for(h = haystack, n = needle; *n != '\0' && *h == *n; h++, n++)
            ;
        if(*n == '\0')
            return (char *)haystack;
    }
    return NULL;
}

/* The calculator has no process environment or shell. */
char *getenv(const char *name)
{
    (void)name;
    return NULL;
}

int system(const char *command)
{
    (void)command;
    return -1;
}

/* Unsupported desktop-style temporary files and scanf family. */
FILE *tmpfile(void)
{
    return NULL;
}

int fscanf(FILE *stream, const char *format, ...)
{
    (void)stream;
    (void)format;
    return EOF;
}

int sscanf(const char *input, const char *format, ...)
{
    (void)input;
    (void)format;
    return EOF;
}

/* Keep PicoC time.h linkable; formatting can be filled in later. */
size_t strftime(char *out, size_t max, const char *format, const struct tm *tm)
{
    (void)format;
    (void)tm;
    if(out != NULL && max > 0)
        out[0] = '\0';
    return 0;
}
