/* Compact standalone SHA-1 backend for PythonUltra.
 *
 * This implementation is intentionally small and dependency-free so the
 * fx-CG50 can expose hashlib.sha1() without bringing in an SSL stack.
 */

#ifndef PYTHONULTRA_SHA1_H
#define PYTHONULTRA_SHA1_H

#include <stddef.h>
#include <stdint.h>

#define SHA1_BLOCK_SIZE 20

typedef struct {
    uint8_t data[64];
    uint32_t datalen;
    uint64_t bitlen;
    uint32_t state[5];
} CRYAL_SHA1_CTX;

void sha1_init(CRYAL_SHA1_CTX *ctx);
void sha1_update(CRYAL_SHA1_CTX *ctx, const uint8_t *data, size_t len);
void sha1_final(CRYAL_SHA1_CTX *ctx, uint8_t hash[SHA1_BLOCK_SIZE]);

#endif
