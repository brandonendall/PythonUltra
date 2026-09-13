/* Small libc functions missing from the fx-CG50 target runtime. */

#include <stddef.h>

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
