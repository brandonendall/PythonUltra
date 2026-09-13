"""Host smoke tests for the frozen fx-CG50 pygame compatibility layer."""

import io
import os
import sys
import types
import unittest


class _RawEvent:
    def __init__(self, event_type, key=0, shift=False, alpha=False):
        self.type = event_type
        self.key = key
        self.shift = shift
        self.alpha = alpha


class _Image:
    def __init__(self, width, height, data):
        self.width = width
        self.height = height
        self.data = data


def _fake_gint():
    module = types.ModuleType("gint")
    key_names = (
        "F1 F2 F3 F4 F5 F6 SHIFT OPTN VARS MENU LEFT UP ALPHA SQUARE "
        "POWER EXIT DOWN RIGHT XOT LOG LN SIN COS TAN FRAC FD LEFTP RIGHTP "
        "COMMA ARROW 7 8 9 DEL 4 5 6 MUL DIV 1 2 3 ADD SUB 0 DOT EXP NEG "
        "EXE ACON"
    ).split()
    for index, name in enumerate(key_names, 1000):
        setattr(module, "KEY_" + name, index)
    module.KEYEV_NONE = 0
    module.KEYEV_DOWN = 1
    module.KEYEV_UP = 2
    module.KEYEV_HOLD = 3
    module.DWIDTH = 396
    module.DHEIGHT = 224
    module.C_NONE = -1
    module.calls = []
    module.events = []
    module.down = set()

    module.__init__ = lambda: module.calls.append(("init",))
    module.image_rgb565 = lambda w, h, data: _Image(w, h, data)
    module.dclear = lambda color: module.calls.append(("clear", color))
    module.dupdate = lambda: module.calls.append(("update",))
    module.drect = lambda *args: module.calls.append(("rect",) + args)
    module.drect_border = lambda *args: module.calls.append(("rect_border",) + args)
    module.dpixel = lambda *args: module.calls.append(("pixel",) + args)
    module.dgetpixel = lambda x, y: 0
    module.dline = lambda *args: module.calls.append(("line",) + args)
    module.dcircle = lambda *args: module.calls.append(("circle",) + args)
    module.dellipse = lambda *args: module.calls.append(("ellipse",) + args)
    module.dpoly = lambda *args: module.calls.append(("poly",) + args)
    module.dtext = lambda *args: module.calls.append(("text",) + args)
    module.dimage = lambda *args: module.calls.append(("image",) + args)
    module.dsubimage = lambda *args: module.calls.append(("subimage",) + args)
    module.keydown = lambda key: key in module.down
    module.clearevents = lambda: module.events.clear()
    module.pollevent = lambda: module.events.pop(0) if module.events else _RawEvent(module.KEYEV_NONE)
    return module


FAKE_GINT = _fake_gint()
sys.modules["gint"] = FAKE_GINT
MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ports/sh/modules"))
sys.path.insert(0, MODULE_DIR)

import pygame


class PygameCompatTests(unittest.TestCase):
    def setUp(self):
        FAKE_GINT.calls[:] = []
        FAKE_GINT.events[:] = []
        FAKE_GINT.down.clear()
        pygame.event.clear()

    def test_display_and_drawing_use_gint(self):
        self.assertEqual(pygame.init(), (2, 0))
        screen = pygame.display.set_mode((800, 600))
        self.assertEqual(screen.get_size(), (396, 224))
        screen.fill("navy")
        pygame.draw.rect(screen, "red", (2, 3, 10, 8))
        pygame.draw.line(screen, "white", (0, 0), (5, 5), 2)
        pygame.display.flip()
        call_names = [item[0] for item in FAKE_GINT.calls]
        self.assertIn("clear", call_names)
        self.assertIn("rect", call_names)
        self.assertIn("line", call_names)
        self.assertIn("update", call_names)

    def test_rect_geometry(self):
        rect = pygame.Rect(10, 20, 30, 40)
        rect.center = (100, 90)
        self.assertEqual(rect.center, (100, 90))
        self.assertTrue(rect.colliderect((90, 80, 30, 30)))
        self.assertFalse(rect.colliderect((200, 200, 2, 2)))
        moved = rect.move(3, -4)
        self.assertEqual(moved.topleft, (rect.x + 3, rect.y - 4))

    def test_offscreen_surface_and_blit(self):
        source = pygame.Surface((4, 3))
        source.fill((255, 0, 0))
        source.set_at((1, 1), (0, 255, 0))
        self.assertGreater(source.get_at((1, 1)).g, 240)
        target = pygame.Surface((8, 8))
        target.blit(source, (2, 2))
        self.assertGreater(target.get_at((3, 3)).g, 240)
        pygame.draw.circle(target, "blue", (4, 4), 2)
        pygame.draw.polygon(target, "white", [(0, 0), (3, 0), (1, 3)])

    def test_screen_blit_honors_colorkey_on_image_backed_surface(self):
        screen = pygame.display.set_mode((396, 224))
        source = pygame.Surface((2, 1))
        source.set_at((0, 0), (0, 0, 0))
        source.set_at((1, 0), (255, 0, 0))
        source._image = FAKE_GINT.image_rgb565(2, 1, source._data)
        source.set_colorkey((0, 0, 0))

        FAKE_GINT.calls[:] = []
        screen.blit(source, (10, 20))

        call_names = [item[0] for item in FAKE_GINT.calls]
        self.assertNotIn("image", call_names)
        self.assertNotIn("subimage", call_names)
        pixel_calls = [item for item in FAKE_GINT.calls if item[0] == "pixel"]
        self.assertEqual(len(pixel_calls), 1)
        self.assertEqual(pixel_calls[0][1:3], (11, 20))

    def test_events_and_pressed_keys(self):
        posted = pygame.event.Event(pygame.USEREVENT, answer=42)
        pygame.event.post(posted)
        self.assertEqual(pygame.event.get()[0].answer, 42)

        FAKE_GINT.events.append(_RawEvent(
            FAKE_GINT.KEYEV_DOWN, FAKE_GINT.KEY_3, alpha=True))
        translated = pygame.event.get()[0]
        self.assertEqual(translated.type, pygame.KEYDOWN)
        self.assertEqual(translated.key, pygame.K_w)
        self.assertEqual(translated.unicode, "w")

        FAKE_GINT.down.add(FAKE_GINT.KEY_3)
        self.assertTrue(pygame.key.get_pressed()[pygame.K_w])
        FAKE_GINT.events.append(_RawEvent(
            FAKE_GINT.KEYEV_DOWN, FAKE_GINT.KEY_EXIT))
        self.assertEqual(pygame.event.get()[0].type, pygame.QUIT)

    def test_font_render_and_image_loader(self):
        screen = pygame.display.set_mode((396, 224))
        rendered = pygame.font.Font(None, 12).render("Hello", True, "black")
        screen.blit(rendered, (4, 5))
        self.assertIn("text", [item[0] for item in FAKE_GINT.calls])

        ppm = b"P6\n2 1\n255\n" + bytes((255, 0, 0, 0, 0, 255))
        loaded = pygame.image.load(io.BytesIO(ppm))
        self.assertEqual(loaded.get_size(), (2, 1))
        self.assertGreater(loaded.get_at((0, 0)).r, 240)
        self.assertGreater(loaded.get_at((1, 0)).b, 240)

    def test_clock_and_sprites(self):
        clock = pygame.time.Clock()
        self.assertGreaterEqual(clock.tick(), 0)

        class Moving(pygame.sprite.Sprite):
            def __init__(self, x):
                pygame.sprite.Sprite.__init__(self)
                self.image = pygame.Surface((4, 4))
                self.rect = self.image.get_rect(topleft=(x, 0))
                self.updates = 0

            def update(self):
                self.updates += 1

        left, right = Moving(0), Moving(2)
        group = pygame.sprite.Group(left, right)
        group.update()
        self.assertEqual(left.updates, 1)
        self.assertEqual(pygame.sprite.spritecollide(left, group, False), [left, right])
        left.kill()
        self.assertNotIn(left, group)

    def test_real_submodule_imports(self):
        from pygame.locals import K_LEFT
        from pygame.sprite import Group as ImportedGroup
        from pygame.time import Clock as ImportedClock
        self.assertEqual(K_LEFT, pygame.K_LEFT)
        self.assertIs(ImportedGroup, pygame.Group)
        self.assertIs(ImportedClock, pygame.Clock)


if __name__ == "__main__":
    unittest.main()
