/* Allocation-free RGB565 color-key blit. Shared with host pixel tests. */
#ifndef PYTHONULTRA_COLORKEY_H
#define PYTHONULTRA_COLORKEY_H
#include <stdint.h>
#include <stddef.h>

static void pe_blit_rgb565_key(uint16_t *dest, int dw, int dh,
    int clip_left, int clip_top, int clip_right, int clip_bottom,
    uint8_t const *source, int sw, int sh, int stride,
    int dx, int dy, int sx, int sy, int width, int height, uint16_t key)
{
    /* Wide arithmetic keeps extreme user coordinates safe before clipping. */
    int64_t left = 0, top = 0, right = width, bottom = height;
    if(clip_left < 0) clip_left = 0;
    if(clip_top < 0) clip_top = 0;
    if(clip_right > dw) clip_right = dw;
    if(clip_bottom > dh) clip_bottom = dh;
    if(-(int64_t)sx > left) left = -(int64_t)sx;
    if(-(int64_t)sy > top) top = -(int64_t)sy;
    if((int64_t)clip_left - dx > left) left = (int64_t)clip_left - dx;
    if((int64_t)clip_top - dy > top) top = (int64_t)clip_top - dy;
    if((int64_t)sw - sx < right) right = (int64_t)sw - sx;
    if((int64_t)sh - sy < bottom) bottom = (int64_t)sh - sy;
    if((int64_t)clip_right - dx < right) right = (int64_t)clip_right - dx;
    if((int64_t)clip_bottom - dy < bottom) bottom = (int64_t)clip_bottom - dy;
    if(left >= right || top >= bottom) return;
    int count = (int)(right - left), rows = (int)(bottom - top);
    int src_x = (int)((int64_t)sx + left), src_y = (int)((int64_t)sy + top);
    int dst_x = (int)((int64_t)dx + left), dst_y = (int)((int64_t)dy + top);
    uint8_t const *src = source + (size_t)src_y * stride + 2 * src_x;
    uint16_t *dst = dest + (size_t)dst_y * dw + dst_x;
    for(int y = 0; y < rows; y++, src += stride, dst += dw) {
        for(int x = 0; x < count; x++) {
            /* Byte reads also support unaligned/padded image buffers. */
            uint16_t color = ((uint16_t)src[2*x] << 8) | src[2*x+1];
            if(color != key) dst[x] = color;
        }
    }
}
#endif
