/* Compact standalone SHA-1 backend for PythonUltra. */

#include "sha1.h"

static uint32_t rol32(uint32_t value, unsigned count)
{
    return (value << count) | (value >> (32 - count));
}

static void sha1_transform(CRYAL_SHA1_CTX *ctx, const uint8_t data[64])
{
    uint32_t w[80];
    for(int i = 0; i < 16; i++) {
        int j = i * 4;
        w[i] = ((uint32_t)data[j] << 24) |
               ((uint32_t)data[j + 1] << 16) |
               ((uint32_t)data[j + 2] << 8) |
               (uint32_t)data[j + 3];
    }
    for(int i = 16; i < 80; i++)
        w[i] = rol32(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1);

    uint32_t a = ctx->state[0];
    uint32_t b = ctx->state[1];
    uint32_t c = ctx->state[2];
    uint32_t d = ctx->state[3];
    uint32_t e = ctx->state[4];

    for(int i = 0; i < 80; i++) {
        uint32_t f, k;
        if(i < 20) {
            f = (b & c) | ((~b) & d);
            k = 0x5a827999u;
        }
        else if(i < 40) {
            f = b ^ c ^ d;
            k = 0x6ed9eba1u;
        }
        else if(i < 60) {
            f = (b & c) | (b & d) | (c & d);
            k = 0x8f1bbcdcu;
        }
        else {
            f = b ^ c ^ d;
            k = 0xca62c1d6u;
        }
        uint32_t temp = rol32(a, 5) + f + e + k + w[i];
        e = d;
        d = c;
        c = rol32(b, 30);
        b = a;
        a = temp;
    }

    ctx->state[0] += a;
    ctx->state[1] += b;
    ctx->state[2] += c;
    ctx->state[3] += d;
    ctx->state[4] += e;
}

void sha1_init(CRYAL_SHA1_CTX *ctx)
{
    ctx->datalen = 0;
    ctx->bitlen = 0;
    ctx->state[0] = 0x67452301u;
    ctx->state[1] = 0xefcdab89u;
    ctx->state[2] = 0x98badcfeu;
    ctx->state[3] = 0x10325476u;
    ctx->state[4] = 0xc3d2e1f0u;
}

void sha1_update(CRYAL_SHA1_CTX *ctx, const uint8_t *data, size_t len)
{
    for(size_t i = 0; i < len; i++) {
        ctx->data[ctx->datalen++] = data[i];
        if(ctx->datalen == 64) {
            sha1_transform(ctx, ctx->data);
            ctx->bitlen += 512;
            ctx->datalen = 0;
        }
    }
}

void sha1_final(CRYAL_SHA1_CTX *ctx, uint8_t hash[SHA1_BLOCK_SIZE])
{
    uint32_t i = ctx->datalen;
    ctx->data[i++] = 0x80;

    if(i > 56) {
        while(i < 64)
            ctx->data[i++] = 0;
        sha1_transform(ctx, ctx->data);
        i = 0;
    }
    while(i < 56)
        ctx->data[i++] = 0;

    ctx->bitlen += (uint64_t)ctx->datalen * 8;
    for(int j = 0; j < 8; j++)
        ctx->data[63 - j] = (uint8_t)(ctx->bitlen >> (j * 8));
    sha1_transform(ctx, ctx->data);

    for(i = 0; i < 5; i++) {
        hash[i * 4] = (uint8_t)(ctx->state[i] >> 24);
        hash[i * 4 + 1] = (uint8_t)(ctx->state[i] >> 16);
        hash[i * 4 + 2] = (uint8_t)(ctx->state[i] >> 8);
        hash[i * 4 + 3] = (uint8_t)ctx->state[i];
    }
}
