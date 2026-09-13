"""Pixel oracle for the actual native blitter and Pygame routing/transforms."""
import ctypes
import builtins
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import pygame_compat as compat
pygame, gint = compat.pygame, compat.FAKE_GINT
ROOT = Path(__file__).resolve().parents[3]


class ColorKeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        source = Path(cls.temp.name) / 'blit.c'
        source.write_text('#define static\n#include "ports/sh/colorkey.h"\n')
        library = Path(cls.temp.name) / 'blit.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-I' + str(ROOT), str(source), '-o', str(library)], check=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.native = cls.lib.pe_blit_rgb565_key
        cls.native.restype = None
        cls.native.argtypes = ([ctypes.POINTER(ctypes.c_uint16)] + [ctypes.c_int] * 6
                               + [ctypes.POINTER(ctypes.c_uint8)] + [ctypes.c_int] * 9
                               + [ctypes.c_uint16])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.fb = (ctypes.c_uint16 * (396 * 224))()
        self.calls = 0
        self.old_pixels = gint.dpixel
        gint.dsubimage_colorkey = self.draw_key
        gint.dpixel = lambda *args: self.fail('color-key blit used Python dpixel')
        self.screen = pygame.display.set_mode((396, 224))

    def tearDown(self):
        del gint.dsubimage_colorkey
        gint.dpixel = self.old_pixels

    def draw_key(self, dx, dy, image, sx, sy, w, h, key):
        self.calls += 1
        raw = (ctypes.c_uint8 * len(image.data)).from_buffer(image.data)
        self.native(self.fb, 396, 224, 0, 0, 396, 224, raw,
                    image.width, image.height, image.width * 2,
                    dx, dy, sx, sy, w, h, key)

    def sprite(self, w=56, h=56):
        s = pygame.Surface((w, h))
        s._image.format = 0
        for y in range(h):
            for x in range(w):
                s._put565(x, y, 0 if (x + y) % 3 == 0 else 0xf800)
        s.set_colorkey((0, 0, 0))
        return s

    def test_56_pixel_sprite_moves_across_screen_in_one_native_call(self):
        sprite = self.sprite()
        for x in range(-56, 397, 7):
            ctypes.memset(self.fb, 0x21, ctypes.sizeof(self.fb))
            self.calls = 0
            affected = self.screen.blit(sprite, (x, 83))
            self.assertEqual(self.calls, int(affected.w > 0 and affected.h > 0))
            for sy in range(56):
                for tx in range(396):
                    sx = tx - x
                    expected = 0xf800 if 0 <= sx < 56 and (sx + sy) % 3 else 0x2121
                    self.assertEqual(self.fb[(83 + sy) * 396 + tx], expected)

    def test_shipped_motion_demo_survives_repeated_builtin_import_init(self):
        # MicroPython's enabled builtin-init hook calls gint.__init__ on each
        # import. That clears VRAM white; desktop Python imports do not do so.
        names = ('__init__', 'dclear', 'dupdate', 'image_rgb565')
        saved = {name: getattr(gint, name) for name in names}
        original_import = builtins.__import__
        old_get, old_tick = pygame.event.get, pygame.Clock.tick
        old_clip = self.screen.get_clip()
        frames = []
        gint.C_WHITE = 0xffff
        def clear(color):
            for i in range(len(self.fb)):
                self.fb[i] = color
        def make_image(w, h, data):
            image = saved['image_rgb565'](w, h, data)
            image.format = 0
            return image
        def importing(name, *args, **kwargs):
            result = original_import(name, *args, **kwargs)
            if name == 'gint':
                gint.__init__()
            return result
        events = iter(([], [], [pygame.event.Event(pygame.QUIT)]))
        try:
            self.screen.set_clip(None)
            gint.dclear = clear
            gint.__init__ = lambda: clear(0xffff)
            gint.image_rgb565 = make_image
            gint.dupdate = lambda: frames.append(list(self.fb))
            pygame.event.get = lambda: next(events)
            pygame.Clock.tick = lambda *args: 0
            builtins.__import__ = importing
            code = (ROOT / 'ports/sh/examples/colorkey_motion.py').read_text()
            exec(compile(code, 'colorkey_motion.py', 'exec'), {'__name__': '__main__'})
        finally:
            builtins.__import__ = original_import
            pygame.event.get, pygame.Clock.tick = old_get, old_tick
            self.screen.set_clip(old_clip)
            for name, value in saved.items():
                setattr(gint, name, value)
        self.assertGreaterEqual(len(frames), 2)
        for frame in frames:
            self.assertEqual(frame[50 * 396 + 10], pygame._color565((24, 48, 80)))
        self.assertTrue(any(pygame._color565((0, 255, 255)) in frame for frame in frames),
                        'No cyan sprite entered the visible screen')

    def test_source_area_and_destination_clip_agree_with_offscreen(self):
        sprite = self.sprite(8, 7)
        self.screen.set_clip((3, 2, 8, 7))
        target = pygame.Surface((396, 224))
        target.set_clip((3, 2, 8, 7))
        for area, dest in [((-2, -1, 8, 7), (0, 0)), ((2, 2, 20, 20), (5, 4)), ((0, 0, 8, 7), (-2, -2))]:
            ctypes.memset(self.fb, 0, ctypes.sizeof(self.fb))
            target._data = bytearray(396 * 224 * 2)
            a = self.screen.blit(sprite, dest, area)
            b = target.blit(sprite, dest, area)
            self.assertEqual(a, b)
            for y in range(16):
                for x in range(20):
                    self.assertEqual(self.fb[y*396+x], target._get565(x, y))

    def test_buffer_edits_and_key_changes_are_not_cached(self):
        sprite = self.sprite(2, 1)
        self.screen.blit(sprite, (0, 0))
        sprite.get_buffer()[0] = 0x07
        sprite.get_buffer()[1] = 0xe0
        self.screen.blit(sprite, (0, 0))
        self.assertEqual(self.fb[0], 0x07e0)
        sprite.set_colorkey((0, 255, 0))
        self.fb[0] = 0xffff
        self.screen.blit(sprite, (0, 0))
        self.assertEqual(self.fb[0], 0xffff)
        sprite.set_colorkey(None)
        gint.calls.clear()
        self.screen.blit(sprite, (0, 0))
        self.assertEqual(gint.calls[-1][0], 'subimage')

    def test_transforms_keep_nonblack_key_and_alpha(self):
        sprite = self.sprite(4, 3)
        sprite.set_colorkey((255, 0, 255))
        sprite.set_alpha(120)
        for result in [pygame.transform.flip(sprite, True, False),
                       pygame.transform.scale(sprite, (8, 6)),
                       pygame.transform.rotate(sprite, 45),
                       pygame.transform.rotozoom(sprite, 45, 0.5)]:
            self.assertEqual(result._colorkey, 0xf81f)
            self.assertEqual(result.get_alpha(), 120)
        rotated = pygame.transform.rotate(sprite, 45)
        self.assertIn(0xf81f, [rotated._get565(x,y) for y in range(rotated._h) for x in range(rotated._w)])

    def test_native_clipping_stride_extreme_coordinates_and_guards(self):
        rng = random.Random(42)
        dw, dh, sw, sh, stride = 16, 12, 6, 5, 16
        raw = bytearray(stride * sh)
        for y in range(sh):
            for x in range(sw):
                value = 0 if (x+y)%2 else 0x07e0
                raw[y*stride+2*x:y*stride+2*x+2] = value.to_bytes(2, 'big')
        buf = (ctypes.c_uint8 * len(raw)).from_buffer(raw)
        for i in range(150):
            dx, dy, sx, sy = [rng.randint(-10, 20) for _ in range(4)]
            if i == 0: dx = 2147483647
            if i == 1: sx = -2147483648
            w, h = rng.randint(-1, 20), rng.randint(-1, 20)
            clip = (2, 1, 14, 10)
            guard = (ctypes.c_uint16 * (dw*dh+2))(*([0xbeef]*(dw*dh+2)))
            dst = ctypes.cast(ctypes.byref(guard, 2), ctypes.POINTER(ctypes.c_uint16))
            self.native(dst, dw, dh, *clip, buf, sw, sh, stride, dx, dy, sx, sy, w, h, 0)
            expected = [0xbeef]*(dw*dh)
            for oy in range(max(0,h)):
                for ox in range(max(0,w)):
                    x,y,rx,ry = dx+ox,dy+oy,sx+ox,sy+oy
                    if clip[0] <= x < clip[2] and clip[1] <= y < clip[3] and 0 <= rx < sw and 0 <= ry < sh and (rx+ry)%2 == 0:
                        expected[y*dw+x] = 0x07e0
            self.assertEqual(list(guard)[1:-1], expected)
            self.assertEqual((guard[0],guard[-1]), (0xbeef,0xbeef))


if __name__ == '__main__':
    unittest.main()
