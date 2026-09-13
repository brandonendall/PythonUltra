"""Regression tests for fx-CG50 pygame behavior seen on real hardware."""

import io
import os
import struct
import sys
import unittest


HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)

# Reuse the fake gint environment from the main compatibility test.
import pygame_compat as compat

pygame = compat.pygame


def bmp24(width, height):
    """Return a minimal uncompressed 24-bit BMP of the requested dimensions."""
    stride = ((width * 3 + 3) // 4) * 4
    pixel_bytes = stride * height
    header = bytearray(54)
    header[0:2] = b"BM"
    struct.pack_into("<I", header, 2, 54 + pixel_bytes)
    struct.pack_into("<I", header, 10, 54)
    struct.pack_into("<I", header, 14, 40)
    struct.pack_into("<i", header, 18, width)
    struct.pack_into("<i", header, 22, height)
    struct.pack_into("<H", header, 26, 1)
    struct.pack_into("<H", header, 28, 24)
    struct.pack_into("<I", header, 34, pixel_bytes)
    return bytes(header) + bytes(pixel_bytes)


class CG50SurfaceRegressionTests(unittest.TestCase):
    def test_convert_alpha_copies_pixels_without_slice_assignment(self):
        source = pygame.Surface((3, 2))
        source.fill((12, 34, 56))
        source.set_at((1, 1), (240, 120, 16))

        converted = source.convert_alpha()
        self.assertIsNot(converted, source)
        self.assertEqual(converted.get_size(), source.get_size())
        self.assertGreater(converted.get_at((1, 1)).r, 230)
        self.assertTrue(converted.get_flags() & pygame.SRCALPHA)

    def test_56x56_24bit_bmp_loads(self):
        loaded = pygame.image.load(io.BytesIO(bmp24(56, 56)))
        self.assertEqual(loaded.get_size(), (56, 56))

    def test_oversized_bmp_is_rejected_before_surface_allocation(self):
        for size in ((57, 56), (56, 57), (396, 224)):
            with self.subTest(size=size):
                with self.assertRaisesRegex(pygame.error, "56x56 image limit"):
                    pygame.image.load(io.BytesIO(bmp24(*size)))

    def test_patched_source_avoids_bytearray_slice_copy(self):
        module_path = os.path.abspath(os.path.join(
            HERE, "../../../ports/sh/modules/pygame/__init__.py"))
        with open(module_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn("result._data[:] = self._data", source)
        self.assertNotIn("self._data[start:start + len(row)] = row", source)
        self.assertIn('raise error("BMP exceeds fx-CG50 56x56 image limit")', source)


if __name__ == "__main__":
    unittest.main()
