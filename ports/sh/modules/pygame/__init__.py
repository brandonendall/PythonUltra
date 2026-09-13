"""Small pygame-compatible layer for PythonExtra on Casio calculators.

This is intentionally a game-learning subset, not SDL.  It keeps the familiar
pygame API while drawing through gint and using RGB565 surfaces in calculator
memory.  Audio, networking, joysticks and desktop window management are out of
scope for this embedded port.
"""

import math as _math
import time as _pytime
import gint as _gint


__version__ = "0.1.1-cg50"


class error(Exception):
    pass


# Event types and common flags use pygame's normal numeric values where that is
# useful to portable programs.  Key constants are translated to gint below.
NOEVENT = 0
QUIT = 0x100
KEYDOWN = 0x300
KEYUP = 0x301
USEREVENT = 0x8000
NUMEVENTS = 0xffff

FULLSCREEN = 0x00000001
DOUBLEBUF = 0x40000000
HWSURFACE = 0x00000001
SRCALPHA = 0x00010000
RLEACCEL = 0x00004000

KMOD_NONE = 0x0000
KMOD_SHIFT = 0x0003
KMOD_CTRL = 0x00c0
KMOD_ALT = 0x0300

K_UNKNOWN = 0
K_BACKSPACE = _gint.KEY_DEL
K_TAB = _gint.KEY_OPTN
K_RETURN = _gint.KEY_EXE
K_ESCAPE = _gint.KEY_EXIT
K_SPACE = _gint.KEY_EXE
K_DELETE = _gint.KEY_DEL
K_UP = _gint.KEY_UP
K_DOWN = _gint.KEY_DOWN
K_LEFT = _gint.KEY_LEFT
K_RIGHT = _gint.KEY_RIGHT
K_F1 = _gint.KEY_F1
K_F2 = _gint.KEY_F2
K_F3 = _gint.KEY_F3
K_F4 = _gint.KEY_F4
K_F5 = _gint.KEY_F5
K_F6 = _gint.KEY_F6

K_0 = ord("0")
K_1 = ord("1")
K_2 = ord("2")
K_3 = ord("3")
K_4 = ord("4")
K_5 = ord("5")
K_6 = ord("6")
K_7 = ord("7")
K_8 = ord("8")
K_9 = ord("9")

K_a = ord("a")
K_b = ord("b")
K_c = ord("c")
K_d = ord("d")
K_e = ord("e")
K_f = ord("f")
K_g = ord("g")
K_h = ord("h")
K_i = ord("i")
K_j = ord("j")
K_k = ord("k")
K_l = ord("l")
K_m = ord("m")
K_n = ord("n")
K_o = ord("o")
K_p = ord("p")
K_q = ord("q")
K_r = ord("r")
K_s = ord("s")
K_t = ord("t")
K_u = ord("u")
K_v = ord("v")
K_w = ord("w")
K_x = ord("x")
K_y = ord("y")
K_z = ord("z")


_NAMED_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "aqua": (0, 255, 255),
    "magenta": (255, 0, 255),
    "purple": (128, 0, 128),
    "orange": (255, 165, 0),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "navy": (0, 0, 128),
    "lime": (0, 255, 0),
    "maroon": (128, 0, 0),
    "olive": (128, 128, 0),
    "teal": (0, 128, 128),
    "silver": (192, 192, 192),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "darkgray": (64, 64, 64),
    "lightgray": (192, 192, 192),
    "transparent": (0, 0, 0, 0),
}


def _clamp8(value):
    value = int(value)
    if value < 0:
        return 0
    if value > 255:
        return 255
    return value


class Color:
    def __init__(self, *value):
        if len(value) == 1:
            value = value[0]
        if isinstance(value, Color):
            self.r, self.g, self.b, self.a = value.r, value.g, value.b, value.a
        elif isinstance(value, str):
            name = value.lower().replace(" ", "")
            if name.startswith("#") and len(name) in (7, 9):
                self.r = int(name[1:3], 16)
                self.g = int(name[3:5], 16)
                self.b = int(name[5:7], 16)
                self.a = int(name[7:9], 16) if len(name) == 9 else 255
            elif name in _NAMED_COLORS:
                parts = _NAMED_COLORS[name]
                self.r, self.g, self.b = parts[0], parts[1], parts[2]
                self.a = parts[3] if len(parts) == 4 else 255
            else:
                raise ValueError("unknown color name: " + value)
        elif isinstance(value, int):
            if 0 <= value <= 0xffff:
                self.r = ((value >> 11) & 31) * 255 // 31
                self.g = ((value >> 5) & 63) * 255 // 63
                self.b = (value & 31) * 255 // 31
                self.a = 255
            else:
                self.r = (value >> 16) & 255
                self.g = (value >> 8) & 255
                self.b = value & 255
                self.a = (value >> 24) & 255 if value > 0xffffff else 255
        else:
            parts = tuple(value)
            if len(parts) not in (3, 4):
                raise ValueError("color needs 3 or 4 components")
            self.r, self.g, self.b = map(_clamp8, parts[:3])
            self.a = _clamp8(parts[3]) if len(parts) == 4 else 255

    def __len__(self):
        return 4

    def __iter__(self):
        return iter((self.r, self.g, self.b, self.a))

    def __getitem__(self, index):
        return (self.r, self.g, self.b, self.a)[index]

    def __repr__(self):
        return "Color(%d, %d, %d, %d)" % (self.r, self.g, self.b, self.a)

    def __eq__(self, other):
        try:
            other = Color(other)
            return tuple(self) == tuple(other)
        except (TypeError, ValueError):
            return False

    def normalize(self):
        return (self.r / 255, self.g / 255, self.b / 255, self.a / 255)

    def correct_gamma(self, gamma):
        return Color(
            int(255 * (self.r / 255) ** gamma),
            int(255 * (self.g / 255) ** gamma),
            int(255 * (self.b / 255) ** gamma),
            self.a,
        )


def _color565(value):
    if isinstance(value, int) and 0 <= value <= 0xffff:
        return value
    color = value if isinstance(value, Color) else Color(value)
    return ((color.r & 0xf8) << 8) | ((color.g & 0xfc) << 3) | (color.b >> 3)


def _color_from_565(value):
    return Color(value & 0xffff)


class Rect:
    def __init__(self, *args):
        if len(args) == 1:
            value = args[0]
            if isinstance(value, Rect):
                values = (value.x, value.y, value.w, value.h)
            else:
                values = tuple(value)
        elif len(args) == 2:
            values = tuple(args[0]) + tuple(args[1])
        else:
            values = args
        if len(values) != 4:
            raise TypeError("Rect needs (x, y, width, height)")
        self.x, self.y, self.w, self.h = map(int, values)

    def __len__(self):
        return 4

    def __iter__(self):
        return iter((self.x, self.y, self.w, self.h))

    def __getitem__(self, index):
        return (self.x, self.y, self.w, self.h)[index]

    def __setitem__(self, index, value):
        values = [self.x, self.y, self.w, self.h]
        values[index] = int(value)
        self.x, self.y, self.w, self.h = values

    def __repr__(self):
        return "<rect(%d, %d, %d, %d)>" % (self.x, self.y, self.w, self.h)

    def __eq__(self, other):
        try:
            return tuple(self) == tuple(Rect(other))
        except (TypeError, ValueError):
            return False

    def __bool__(self):
        return self.w != 0 and self.h != 0

    def copy(self):
        return Rect(self)

    def update(self, *args):
        other = Rect(*args)
        self.x, self.y, self.w, self.h = other.x, other.y, other.w, other.h

    @property
    def width(self):
        return self.w

    @width.setter
    def width(self, value):
        self.w = int(value)

    @property
    def height(self):
        return self.h

    @height.setter
    def height(self, value):
        self.h = int(value)

    @property
    def left(self):
        return self.x

    @left.setter
    def left(self, value):
        self.x = int(value)

    @property
    def right(self):
        return self.x + self.w

    @right.setter
    def right(self, value):
        self.x = int(value) - self.w

    @property
    def top(self):
        return self.y

    @top.setter
    def top(self, value):
        self.y = int(value)

    @property
    def bottom(self):
        return self.y + self.h

    @bottom.setter
    def bottom(self, value):
        self.y = int(value) - self.h

    @property
    def centerx(self):
        return self.x + self.w // 2

    @centerx.setter
    def centerx(self, value):
        self.x = int(value) - self.w // 2

    @property
    def centery(self):
        return self.y + self.h // 2

    @centery.setter
    def centery(self, value):
        self.y = int(value) - self.h // 2

    @property
    def center(self):
        return (self.centerx, self.centery)

    @center.setter
    def center(self, value):
        self.centerx, self.centery = value

    @property
    def size(self):
        return (self.w, self.h)

    @size.setter
    def size(self, value):
        self.w, self.h = map(int, value)

    @property
    def topleft(self):
        return (self.left, self.top)

    @topleft.setter
    def topleft(self, value):
        self.left, self.top = value

    @property
    def topright(self):
        return (self.right, self.top)

    @topright.setter
    def topright(self, value):
        self.right, self.top = value

    @property
    def bottomleft(self):
        return (self.left, self.bottom)

    @bottomleft.setter
    def bottomleft(self, value):
        self.left, self.bottom = value

    @property
    def bottomright(self):
        return (self.right, self.bottom)

    @bottomright.setter
    def bottomright(self, value):
        self.right, self.bottom = value

    @property
    def midtop(self):
        return (self.centerx, self.top)

    @midtop.setter
    def midtop(self, value):
        self.centerx, self.top = value

    @property
    def midbottom(self):
        return (self.centerx, self.bottom)

    @midbottom.setter
    def midbottom(self, value):
        self.centerx, self.bottom = value

    @property
    def midleft(self):
        return (self.left, self.centery)

    @midleft.setter
    def midleft(self, value):
        self.left, self.centery = value

    @property
    def midright(self):
        return (self.right, self.centery)

    @midright.setter
    def midright(self, value):
        self.right, self.centery = value

    def move(self, *offset):
        if len(offset) == 1:
            offset = offset[0]
        return Rect(self.x + int(offset[0]), self.y + int(offset[1]), self.w, self.h)

    def move_ip(self, *offset):
        if len(offset) == 1:
            offset = offset[0]
        self.x += int(offset[0])
        self.y += int(offset[1])

    def inflate(self, x, y):
        result = self.copy()
        result.inflate_ip(x, y)
        return result

    def inflate_ip(self, x, y):
        old_center = self.center
        self.w += int(x)
        self.h += int(y)
        self.center = old_center

    def normalize(self):
        if self.w < 0:
            self.x += self.w
            self.w = -self.w
        if self.h < 0:
            self.y += self.h
            self.h = -self.h

    def clamp(self, other):
        result = self.copy()
        result.clamp_ip(other)
        return result

    def clamp_ip(self, other):
        other = Rect(other)
        if self.w >= other.w:
            self.centerx = other.centerx
        else:
            if self.left < other.left:
                self.left = other.left
            if self.right > other.right:
                self.right = other.right
        if self.h >= other.h:
            self.centery = other.centery
        else:
            if self.top < other.top:
                self.top = other.top
            if self.bottom > other.bottom:
                self.bottom = other.bottom

    def clip(self, other):
        other = Rect(other)
        left = max(self.left, other.left)
        top = max(self.top, other.top)
        right = min(self.right, other.right)
        bottom = min(self.bottom, other.bottom)
        if right <= left or bottom <= top:
            return Rect(left, top, 0, 0)
        return Rect(left, top, right - left, bottom - top)

    def union(self, other):
        other = Rect(other)
        left = min(self.left, other.left)
        top = min(self.top, other.top)
        right = max(self.right, other.right)
        bottom = max(self.bottom, other.bottom)
        return Rect(left, top, right - left, bottom - top)

    def union_ip(self, other):
        result = self.union(other)
        self.update(result)

    def unionall(self, rects):
        result = self.copy()
        for item in rects:
            result = result.union(item)
        return result

    def contains(self, other):
        other = Rect(other)
        return (self.left <= other.left and self.top <= other.top and
                self.right >= other.right and self.bottom >= other.bottom)

    def collidepoint(self, *point):
        if len(point) == 1:
            point = point[0]
        x, y = point
        return self.left <= x < self.right and self.top <= y < self.bottom

    def colliderect(self, other):
        other = Rect(other)
        return (self.left < other.right and self.right > other.left and
                self.top < other.bottom and self.bottom > other.top)

    def collidelist(self, rects):
        for index, other in enumerate(rects):
            if self.colliderect(other):
                return index
        return -1

    def collidelistall(self, rects):
        return [i for i, other in enumerate(rects) if self.colliderect(other)]


class Surface:
    def __init__(self, size, flags=0, depth=0, masks=None, _screen=False,
                 _image=None):
        self._w, self._h = map(int, size)
        if self._w <= 0 or self._h <= 0:
            raise ValueError("Surface dimensions must be positive")
        self._flags = flags
        self._screen = bool(_screen)
        self._alpha = None
        self._colorkey = None
        self._clip = Rect(0, 0, self._w, self._h)
        self._text = None
        self._text_color = None
        self._text_background = None
        if self._screen:
            self._data = None
            self._image = None
        elif _image is not None:
            self._data = getattr(_image, "data", None)
            self._image = _image
        else:
            self._data = bytearray(self._w * self._h * 2)
            self._image = _gint.image_rgb565(self._w, self._h, self._data)

    @classmethod
    def _make_screen(cls):
        return cls((int(_gint.DWIDTH), int(_gint.DHEIGHT)), HWSURFACE,
                   _screen=True)

    @classmethod
    def _from_gint_image(cls, image):
        return cls((int(image.width), int(image.height)), _image=image)

    def __repr__(self):
        return "<Surface(%dx%dx16%s)>" % (
            self._w, self._h, ", display" if self._screen else "")

    def get_size(self):
        return (self._w, self._h)

    def get_width(self):
        return self._w

    def get_height(self):
        return self._h

    def get_rect(self, **kwargs):
        result = Rect(0, 0, self._w, self._h)
        for name, value in kwargs.items():
            setattr(result, name, value)
        return result

    def get_flags(self):
        return self._flags

    def get_bitsize(self):
        return 16

    def get_bytesize(self):
        return 2

    def get_pitch(self):
        return self._w * 2

    def get_buffer(self):
        return memoryview(self._data) if self._data is not None else None

    def get_view(self, kind="2"):
        return self.get_buffer()

    def set_alpha(self, value, flags=0):
        self._alpha = value

    def get_alpha(self):
        return self._alpha

    def set_colorkey(self, color, flags=0):
        self._colorkey = None if color is None else _color565(color)

    def get_colorkey(self):
        return None if self._colorkey is None else _color_from_565(self._colorkey)

    def set_clip(self, rect=None):
        old = self._clip.copy()
        self._clip = Rect(0, 0, self._w, self._h) if rect is None else Rect(rect).clip((0, 0, self._w, self._h))
        return old

    def get_clip(self):
        return self._clip.copy()

    def map_rgb(self, color):
        return _color565(color)

    def unmap_rgb(self, value):
        return _color_from_565(value)

    def lock(self):
        return None

    def unlock(self):
        return None

    def mustlock(self):
        return False

    def get_locked(self):
        return False

    def _put565(self, x, y, color):
        x, y = int(x), int(y)
        if x < 0 or y < 0 or x >= self._w or y >= self._h:
            return
        if self._screen:
            _gint.dpixel(x, y, color)
        else:
            index = 2 * (y * self._w + x)
            self._data[index] = (color >> 8) & 255
            self._data[index + 1] = color & 255

    def _get565(self, x, y):
        x, y = int(x), int(y)
        if x < 0 or y < 0 or x >= self._w or y >= self._h:
            raise IndexError("pixel outside Surface")
        if self._screen:
            return int(_gint.dgetpixel(x, y)) & 0xffff
        index = 2 * (y * self._w + x)
        return (self._data[index] << 8) | self._data[index + 1]

    def set_at(self, pos, color):
        self._put565(pos[0], pos[1], _color565(color))

    def get_at(self, pos):
        return _color_from_565(self._get565(pos[0], pos[1]))

    def fill(self, color, rect=None, special_flags=0):
        color = _color565(color)
        area = Rect(0, 0, self._w, self._h) if rect is None else Rect(rect)
        area = area.clip((0, 0, self._w, self._h))
        if area.w <= 0 or area.h <= 0:
            return area
        if self._screen:
            if area == Rect(0, 0, self._w, self._h):
                _gint.dclear(color)
            else:
                _gint.drect(area.left, area.top, area.right - 1, area.bottom - 1, color)
        else:
            pixel = bytes(((color >> 8) & 255, color & 255))
            row = pixel * area.w
            for y in range(area.top, area.bottom):
                start = 2 * (y * self._w + area.left)
                self._data[start:start + len(row)] = row
        return area

    def blit(self, source, dest, area=None, special_flags=0):
        if not isinstance(source, Surface):
            if hasattr(source, "width") and hasattr(source, "height"):
                source = Surface._from_gint_image(source)
            else:
                raise TypeError("source must be a Surface or gint.image")
        if isinstance(dest, Rect):
            dx, dy = dest.x, dest.y
        else:
            dx, dy = int(dest[0]), int(dest[1])
        src = Rect(0, 0, source._w, source._h) if area is None else Rect(area)
        bounded = src.clip((0, 0, source._w, source._h))
        dx += bounded.x - src.x
        dy += bounded.y - src.y
        src = bounded
        result = Rect(dx, dy, src.w, src.h).clip(self._clip)
        if src.w <= 0 or src.h <= 0 or result.w <= 0 or result.h <= 0:
            return result

        if self._screen and source._text is not None:
            if source._text_background is not None:
                _gint.drect(dx, dy, dx + source._w - 1, dy + source._h - 1,
                            source._text_background)
            _gint.dtext(dx, dy, source._text_color, source._text)
            return result

        # Crop once before either native drawing or software composition.
        src.x += result.x - dx
        src.y += result.y - dy
        src.w, src.h = result.w, result.h
        dx, dy = result.x, result.y
        if self._screen and source._image is not None:
            if source._colorkey is None:
                _gint.dsubimage(dx, dy, source._image, src.x, src.y, src.w, src.h)
                return result
            native_key_blit = getattr(_gint, "dsubimage_colorkey", None)
            if native_key_blit is not None and getattr(source._image, "format", -1) == 0:
                # One native call, with no copied image or stale key cache.
                native_key_blit(dx, dy, source._image, src.x, src.y,
                                src.w, src.h, source._colorkey)
                return result

        # Software copy supports off-screen composition and display snapshots.
        for sy in range(src.h):
            ty = dy + sy
            for sx in range(src.w):
                tx = dx + sx
                color = source._get565(src.x + sx, src.y + sy)
                if source._colorkey is None or color != source._colorkey:
                    self._put565(tx, ty, color)
        return result

    def blits(self, blit_sequence, doreturn=1):
        changed = [self.blit(*item) for item in blit_sequence]
        return changed if doreturn else None

    def copy(self):
        result = Surface((self._w, self._h), self._flags)
        result._alpha = self._alpha
        result._colorkey = self._colorkey
        result._text = self._text
        result._text_color = self._text_color
        result._text_background = self._text_background
        if self._screen:
            for y in range(self._h):
                for x in range(self._w):
                    result._put565(x, y, self._get565(x, y))
        else:
            result._data[:] = self._data
        return result

    def convert(self, surface=None):
        return self.copy()

    def convert_alpha(self, surface=None):
        result = self.copy()
        result._flags |= SRCALPHA
        return result

    def subsurface(self, rect):
        rect = Rect(rect).clip((0, 0, self._w, self._h))
        result = Surface(rect.size, self._flags)
        result.blit(self, (0, 0), rect)
        return result

    def scroll(self, dx=0, dy=0):
        copy = self.copy()
        self.blit(copy, (dx, dy))


class _DisplayInfo:
    def __init__(self):
        self.hw = 1
        self.wm = 0
        self.video_mem = 0
        self.bitsize = 16
        self.bytesize = 2
        self.current_w = int(_gint.DWIDTH)
        self.current_h = int(_gint.DHEIGHT)


class _Display:
    def __init__(self):
        self._surface = None
        self._caption = "PythonUltra pygame"
        self._init = False

    def init(self):
        _gint.__init__()
        self._init = True

    def quit(self):
        self._init = False

    def get_init(self):
        return self._init

    def set_mode(self, size=(0, 0), flags=0, depth=0, display=0, vsync=0):
        if not self._init:
            self.init()
        if self._surface is None:
            self._surface = Surface._make_screen()
        return self._surface

    def get_surface(self):
        return self._surface

    def flip(self):
        _gint.dupdate()

    def update(self, rectangle=None):
        _gint.dupdate()

    def set_caption(self, title, icontitle=None):
        self._caption = str(title)

    def get_caption(self):
        return (self._caption, self._caption)

    def set_icon(self, surface):
        return None

    def Info(self):
        return _DisplayInfo()

    def get_driver(self):
        return "gint"

    def get_window_size(self):
        return (int(_gint.DWIDTH), int(_gint.DHEIGHT))

    def list_modes(self, depth=0, flags=FULLSCREEN, display=0):
        return [self.get_window_size()]

    def mode_ok(self, size, flags=0, depth=0, display=0):
        return 16

    def toggle_fullscreen(self):
        return 1


display = _Display()


def _draw_line(surface, color, start, end):
    x0, y0 = map(int, start)
    x1, y1 = map(int, end)
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        surface._put565(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        twice = 2 * err
        if twice >= dy:
            err += dy
            x0 += sx
        if twice <= dx:
            err += dx
            y0 += sy


class _Draw:
    def line(self, surface, color, start_pos, end_pos, width=1):
        color = _color565(color)
        x1, y1 = map(int, start_pos)
        x2, y2 = map(int, end_pos)
        width = max(1, int(width))
        if surface._screen:
            for offset in range(-(width // 2), (width + 1) // 2):
                if abs(x2 - x1) >= abs(y2 - y1):
                    _gint.dline(x1, y1 + offset, x2, y2 + offset, color)
                else:
                    _gint.dline(x1 + offset, y1, x2 + offset, y2, color)
        else:
            for offset in range(-(width // 2), (width + 1) // 2):
                if abs(x2 - x1) >= abs(y2 - y1):
                    _draw_line(surface, color, (x1, y1 + offset), (x2, y2 + offset))
                else:
                    _draw_line(surface, color, (x1 + offset, y1), (x2 + offset, y2))
        return Rect(min(x1, x2), min(y1, y2), abs(x2 - x1) + 1, abs(y2 - y1) + 1).inflate(width - 1, width - 1)

    aaline = line

    def lines(self, surface, color, closed, points, width=1):
        points = list(points)
        result = Rect(0, 0, 0, 0)
        if len(points) < 2:
            return result
        for index in range(len(points) - 1):
            part = self.line(surface, color, points[index], points[index + 1], width)
            result = part if not result else result.union(part)
        if closed:
            result = result.union(self.line(surface, color, points[-1], points[0], width))
        return result

    aalines = lines

    def rect(self, surface, color, rect, width=0, border_radius=0,
             border_top_left_radius=-1, border_top_right_radius=-1,
             border_bottom_left_radius=-1, border_bottom_right_radius=-1):
        rect = Rect(rect)
        color = _color565(color)
        if rect.w <= 0 or rect.h <= 0:
            return rect
        if surface._screen:
            if width <= 0:
                _gint.drect(rect.left, rect.top, rect.right - 1, rect.bottom - 1, color)
            else:
                width = max(1, min(int(width), rect.w // 2, rect.h // 2))
                for n in range(width):
                    _gint.drect_border(rect.left + n, rect.top + n,
                                       rect.right - 1 - n, rect.bottom - 1 - n,
                                       _gint.C_NONE, 1, color)
        elif width <= 0:
            surface.fill(color, rect)
        else:
            width = max(1, int(width))
            surface.fill(color, (rect.left, rect.top, rect.w, width))
            surface.fill(color, (rect.left, rect.bottom - width, rect.w, width))
            surface.fill(color, (rect.left, rect.top + width, width, rect.h - 2 * width))
            surface.fill(color, (rect.right - width, rect.top + width, width, rect.h - 2 * width))
        return rect

    def circle(self, surface, color, center, radius, width=0,
               draw_top_right=None, draw_top_left=None,
               draw_bottom_left=None, draw_bottom_right=None):
        cx, cy = map(int, center)
        radius = max(0, int(radius))
        color = _color565(color)
        if surface._screen:
            if width <= 0:
                _gint.dcircle(cx, cy, radius, color, color)
            else:
                for n in range(max(1, int(width))):
                    if radius - n >= 0:
                        _gint.dcircle(cx, cy, radius - n, _gint.C_NONE, color)
        else:
            inner = max(0, radius - max(1, int(width))) if width > 0 else 0
            r2, inner2 = radius * radius, inner * inner
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    distance = (x - cx) ** 2 + (y - cy) ** 2
                    if distance <= r2 and (width <= 0 or distance >= inner2):
                        surface._put565(x, y, color)
        return Rect(cx - radius, cy - radius, radius * 2 + 1, radius * 2 + 1)

    def ellipse(self, surface, color, rect, width=0):
        rect = Rect(rect)
        color = _color565(color)
        if rect.w <= 0 or rect.h <= 0:
            return rect
        if surface._screen:
            _gint.dellipse(rect.left, rect.top, rect.right - 1, rect.bottom - 1,
                           color if width <= 0 else _gint.C_NONE, color)
        else:
            cx, cy = rect.center
            rx, ry = max(1, rect.w // 2), max(1, rect.h // 2)
            inner_rx = max(1, rx - max(1, int(width)))
            inner_ry = max(1, ry - max(1, int(width)))
            for y in range(rect.top, rect.bottom):
                for x in range(rect.left, rect.right):
                    outer = ((x - cx) ** 2 * ry * ry + (y - cy) ** 2 * rx * rx) <= rx * rx * ry * ry
                    inner = ((x - cx) ** 2 * inner_ry * inner_ry + (y - cy) ** 2 * inner_rx * inner_rx) < inner_rx * inner_rx * inner_ry * inner_ry
                    if outer and (width <= 0 or not inner):
                        surface._put565(x, y, color)
        return rect

    def polygon(self, surface, color, points, width=0):
        points = [(int(p[0]), int(p[1])) for p in points]
        if len(points) < 3:
            return self.lines(surface, color, True, points, max(1, width))
        color = _color565(color)
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        result = Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
        if surface._screen:
            flat = []
            for point in points:
                flat.extend(point)
            _gint.dpoly(flat, color if width <= 0 else _gint.C_NONE, color)
            if width > 1:
                self.lines(surface, color, True, points, width)
        elif width > 0:
            self.lines(surface, color, True, points, width)
        else:
            # Even/odd scanline fill; small and adequate for sprite surfaces.
            for y in range(result.top, result.bottom):
                intersections = []
                previous = points[-1]
                for current in points:
                    x1, y1 = previous
                    x2, y2 = current
                    if (y1 <= y < y2) or (y2 <= y < y1):
                        intersections.append(x1 + (y - y1) * (x2 - x1) // (y2 - y1))
                    previous = current
                intersections.sort()
                for index in range(0, len(intersections) - 1, 2):
                    for x in range(intersections[index], intersections[index + 1] + 1):
                        surface._put565(x, y, color)
        return result

    def arc(self, surface, color, rect, start_angle, stop_angle, width=1):
        rect = Rect(rect)
        cx, cy = rect.center
        rx, ry = rect.w / 2, rect.h / 2
        steps = max(8, int(abs(stop_angle - start_angle) * max(rx, ry)))
        points = []
        for index in range(steps + 1):
            angle = start_angle + (stop_angle - start_angle) * index / steps
            points.append((cx + int(_math.cos(angle) * rx), cy - int(_math.sin(angle) * ry)))
        return self.lines(surface, color, False, points, width)


draw = _Draw()


def _ticks_ms():
    if hasattr(_pytime, "ticks_ms"):
        return _pytime.ticks_ms()
    return int(_pytime.monotonic() * 1000)


def _ticks_diff(end, start):
    if hasattr(_pytime, "ticks_diff"):
        return _pytime.ticks_diff(end, start)
    return end - start


def _sleep_ms(milliseconds):
    milliseconds = max(0, int(milliseconds))
    if hasattr(_pytime, "sleep_ms"):
        _pytime.sleep_ms(milliseconds)
    else:
        _pytime.sleep(milliseconds / 1000)


_start_ticks = _ticks_ms()


class Clock:
    def __init__(self):
        self._last = _ticks_ms()
        self._time = 0
        self._raw = 0
        self._fps = 0.0
        self._fps_start = self._last
        self._fps_frames = 0

    def tick(self, framerate=0):
        now = _ticks_ms()
        self._raw = max(0, _ticks_diff(now, self._last))
        if framerate:
            target = max(1, 1000 // int(framerate))
            if self._raw < target:
                _sleep_ms(target - self._raw)
                now = _ticks_ms()
        self._time = max(0, _ticks_diff(now, self._last))
        self._last = now
        self._fps_frames += 1
        sample = _ticks_diff(now, self._fps_start)
        if sample >= 1000:
            self._fps = self._fps_frames * 1000.0 / sample
            self._fps_frames = 0
            self._fps_start = now
        return self._time

    tick_busy_loop = tick

    def get_time(self):
        return self._time

    def get_rawtime(self):
        return self._raw

    def get_fps(self):
        return self._fps


class _Time:
    Clock = Clock

    def get_ticks(self):
        return max(0, _ticks_diff(_ticks_ms(), _start_ticks))

    def delay(self, milliseconds):
        start = _ticks_ms()
        _sleep_ms(milliseconds)
        return max(0, _ticks_diff(_ticks_ms(), start))

    wait = delay


time = _Time()


_ALPHA_KEYS = {
    K_a: _gint.KEY_XOT, K_b: _gint.KEY_LOG, K_c: _gint.KEY_LN,
    K_d: _gint.KEY_SIN, K_e: _gint.KEY_COS, K_f: _gint.KEY_TAN,
    K_g: _gint.KEY_FRAC, K_h: _gint.KEY_FD, K_i: _gint.KEY_LEFTP,
    K_j: _gint.KEY_RIGHTP, K_k: _gint.KEY_COMMA, K_l: _gint.KEY_ARROW,
    K_m: _gint.KEY_7, K_n: _gint.KEY_8, K_o: _gint.KEY_9,
    K_p: _gint.KEY_4, K_q: _gint.KEY_5, K_r: _gint.KEY_6,
    K_s: _gint.KEY_MUL, K_t: _gint.KEY_DIV, K_u: _gint.KEY_1,
    K_v: _gint.KEY_2, K_w: _gint.KEY_3, K_x: _gint.KEY_ADD,
    K_y: _gint.KEY_SUB, K_z: _gint.KEY_0,
}
_DIGIT_KEYS = {
    K_0: _gint.KEY_0, K_1: _gint.KEY_1, K_2: _gint.KEY_2,
    K_3: _gint.KEY_3, K_4: _gint.KEY_4, K_5: _gint.KEY_5,
    K_6: _gint.KEY_6, K_7: _gint.KEY_7, K_8: _gint.KEY_8,
    K_9: _gint.KEY_9,
}
_RAW_SPECIAL_KEYS = {
    K_BACKSPACE: _gint.KEY_DEL, K_TAB: _gint.KEY_OPTN,
    K_RETURN: _gint.KEY_EXE, K_ESCAPE: _gint.KEY_EXIT,
    K_UP: _gint.KEY_UP, K_DOWN: _gint.KEY_DOWN,
    K_LEFT: _gint.KEY_LEFT, K_RIGHT: _gint.KEY_RIGHT,
    K_F1: _gint.KEY_F1, K_F2: _gint.KEY_F2, K_F3: _gint.KEY_F3,
    K_F4: _gint.KEY_F4, K_F5: _gint.KEY_F5, K_F6: _gint.KEY_F6,
}
_PHYSICAL_ALPHA = {physical: letter for letter, physical in _ALPHA_KEYS.items()}
_PHYSICAL_DIGIT = {physical: digit for digit, physical in _DIGIT_KEYS.items()}


def _physical_key(keycode):
    if keycode == K_SPACE:
        return _gint.KEY_EXE
    return _ALPHA_KEYS.get(keycode, _DIGIT_KEYS.get(keycode, _RAW_SPECIAL_KEYS.get(keycode, keycode)))


class _PressedKeys:
    def __getitem__(self, keycode):
        try:
            return bool(_gint.keydown(_physical_key(keycode)))
        except (TypeError, ValueError):
            return False

    def __len__(self):
        return 512


class _Key:
    def get_pressed(self):
        return _PressedKeys()

    def get_mods(self):
        mods = KMOD_NONE
        if _gint.keydown(_gint.KEY_SHIFT):
            mods |= KMOD_SHIFT
        if _gint.keydown(_gint.KEY_ALPHA):
            mods |= KMOD_CTRL
        return mods

    def set_mods(self, mods):
        return None

    def name(self, keycode):
        if K_a <= keycode <= K_z:
            return chr(keycode)
        if K_0 <= keycode <= K_9:
            return chr(keycode)
        names = {
            K_UP: "up", K_DOWN: "down", K_LEFT: "left", K_RIGHT: "right",
            K_RETURN: "return", K_ESCAPE: "escape", K_BACKSPACE: "backspace",
            K_F1: "f1", K_F2: "f2", K_F3: "f3", K_F4: "f4",
            K_F5: "f5", K_F6: "f6",
        }
        return names.get(keycode, "unknown key")

    def set_repeat(self, delay=0, interval=0):
        return None

    def get_repeat(self):
        return (0, 0)


key = _Key()


class Event:
    def __init__(self, event_type, attributes=None, **kwargs):
        self.type = int(event_type)
        self.dict = {}
        if attributes:
            self.dict.update(attributes)
        self.dict.update(kwargs)
        for name, value in self.dict.items():
            setattr(self, name, value)

    def __repr__(self):
        return "<Event(%d %r)>" % (self.type, self.dict)


def _translate_event(raw):
    if raw.type == _gint.KEYEV_NONE:
        return None
    if raw.type == _gint.KEYEV_UP:
        event_type = KEYUP
    elif raw.type in (_gint.KEYEV_DOWN, _gint.KEYEV_HOLD):
        event_type = KEYDOWN
    else:
        return None
    if raw.key == _gint.KEY_EXIT and event_type == KEYDOWN:
        return Event(QUIT)

    keycode = raw.key
    unicode_value = ""
    if raw.alpha and raw.key in _PHYSICAL_ALPHA:
        keycode = _PHYSICAL_ALPHA[raw.key]
        unicode_value = chr(keycode)
        if raw.shift:
            unicode_value = unicode_value.upper()
    elif raw.key in _PHYSICAL_DIGIT:
        keycode = _PHYSICAL_DIGIT[raw.key]
        unicode_value = chr(keycode)
    elif raw.key == _gint.KEY_EXE:
        keycode = K_RETURN
        unicode_value = "\r"
    mods = (KMOD_SHIFT if raw.shift else 0) | (KMOD_CTRL if raw.alpha else 0)
    return Event(event_type, key=keycode, mod=mods, unicode=unicode_value,
                 scancode=raw.key, repeat=(raw.type == _gint.KEYEV_HOLD))


_event_queue = []
_next_user_event = USEREVENT


class _Event:
    Event = Event
    EventType = Event

    def pump(self):
        return None

    def post(self, item):
        if not isinstance(item, Event):
            raise TypeError("event must be an Event")
        _event_queue.append(item)
        return True

    def _drain_hardware(self):
        while True:
            raw = _gint.pollevent()
            translated = _translate_event(raw)
            if translated is None:
                break
            _event_queue.append(translated)

    def get(self, eventtype=None, pump=True, exclude=None):
        if pump:
            self._drain_hardware()
        if eventtype is None:
            result = list(_event_queue)
            _event_queue[:] = []
            return result
        wanted = eventtype if isinstance(eventtype, (tuple, list, set)) else (eventtype,)
        result, remaining = [], []
        for item in _event_queue:
            (result if item.type in wanted else remaining).append(item)
        _event_queue[:] = remaining
        return result

    def poll(self):
        values = self.get()
        if not values:
            return Event(NOEVENT)
        first = values[0]
        _event_queue[:0] = values[1:]
        return first

    def wait(self, timeout=0):
        start = _ticks_ms()
        while True:
            item = self.poll()
            if item.type != NOEVENT:
                return item
            if timeout and _ticks_diff(_ticks_ms(), start) >= timeout:
                return Event(NOEVENT)
            _sleep_ms(10)

    def clear(self, eventtype=None, pump=True):
        if eventtype is None:
            _event_queue[:] = []
            _gint.clearevents()
        else:
            self.get(eventtype, pump=pump)

    def peek(self, eventtype=None, pump=True):
        if pump:
            self._drain_hardware()
        if eventtype is None:
            return bool(_event_queue)
        wanted = eventtype if isinstance(eventtype, (tuple, list, set)) else (eventtype,)
        return any(item.type in wanted for item in _event_queue)

    def custom_type(self):
        global _next_user_event
        value = _next_user_event
        _next_user_event += 1
        return value

    def event_name(self, event_type):
        return {NOEVENT: "NoEvent", QUIT: "Quit", KEYDOWN: "KeyDown",
                KEYUP: "KeyUp"}.get(event_type, "UserEvent")


event = _Event()


class _Mouse:
    def get_pos(self):
        return (0, 0)

    def get_pressed(self, num_buttons=3):
        return tuple(False for _ in range(num_buttons))

    def set_visible(self, visible):
        return False

    def get_visible(self):
        return False


mouse = _Mouse()


class Font:
    def __init__(self, file, size):
        self.file = file
        self._size = max(1, int(size))
        self._bold = False
        self._italic = False
        self._underline = False

    def size(self, text):
        text = str(text)
        width = len(text) * max(4, self._size // 2)
        return (max(1, width), self.get_linesize())

    def render(self, text, antialias, color, background=None, wraplength=0):
        text = str(text)
        result = Surface(self.size(text), SRCALPHA)
        result._text = text
        result._text_color = _color565(color)
        result._text_background = None if background is None else _color565(background)
        return result

    def get_height(self):
        return self._size

    def get_linesize(self):
        return self._size + 2

    def get_ascent(self):
        return self._size

    def get_descent(self):
        return -2

    def set_bold(self, value):
        self._bold = bool(value)

    def get_bold(self):
        return self._bold

    def set_italic(self, value):
        self._italic = bool(value)

    def get_italic(self):
        return self._italic

    def set_underline(self, value):
        self._underline = bool(value)

    def get_underline(self):
        return self._underline


class _Font:
    Font = Font

    def __init__(self):
        self._init = False

    def init(self):
        self._init = True

    def quit(self):
        self._init = False

    def get_init(self):
        return self._init

    def SysFont(self, name, size, bold=False, italic=False, constructor=None):
        result = Font(None, size)
        result.set_bold(bold)
        result.set_italic(italic)
        return result

    def get_default_font(self):
        return "gint-default"

    def get_fonts(self):
        return ["gint-default"]

    def match_font(self, name, bold=False, italic=False):
        return None


font = _Font()


def _u16le(data, offset):
    return data[offset] | (data[offset + 1] << 8)


def _u32le(data, offset):
    return (_u16le(data, offset) | (_u16le(data, offset + 2) << 16))


def _i32le(data, offset):
    value = _u32le(data, offset)
    return value - 0x100000000 if value & 0x80000000 else value


def _load_bmp(data):
    if len(data) < 54 or data[:2] != b"BM":
        raise error("not a BMP image")
    offset = _u32le(data, 10)
    width = _i32le(data, 18)
    signed_height = _i32le(data, 22)
    bpp = _u16le(data, 28)
    compression = _u32le(data, 30)
    if width <= 0 or signed_height == 0 or bpp not in (24, 32) or compression != 0:
        raise error("BMP must be uncompressed 24-bit or 32-bit")
    height = abs(signed_height)
    result = Surface((width, height))
    stride = ((width * bpp + 31) // 32) * 4
    bytes_per_pixel = bpp // 8
    for y in range(height):
        source_y = height - 1 - y if signed_height > 0 else y
        row = offset + source_y * stride
        for x in range(width):
            pos = row + x * bytes_per_pixel
            if pos + bytes_per_pixel > len(data):
                raise error("truncated BMP image")
            blue, green, red = data[pos], data[pos + 1], data[pos + 2]
            result._put565(x, y, _color565((red, green, blue)))
    return result


def _load_ppm(data):
    tokens = []
    index = 0
    while len(tokens) < 4 and index < len(data):
        while index < len(data) and data[index] in b" \t\r\n":
            index += 1
        if index < len(data) and data[index] == 35:
            while index < len(data) and data[index] not in b"\r\n":
                index += 1
            continue
        start = index
        while index < len(data) and data[index] not in b" \t\r\n":
            index += 1
        tokens.append(data[start:index])
    if len(tokens) != 4 or tokens[0] != b"P6":
        raise error("not a binary PPM image")
    width, height, maximum = int(tokens[1]), int(tokens[2]), int(tokens[3])
    if width <= 0 or height <= 0 or maximum <= 0 or maximum > 255:
        raise error("unsupported PPM dimensions or color depth")
    while index < len(data) and data[index] in b" \t\r\n":
        index += 1
    if len(data) - index < width * height * 3:
        raise error("truncated PPM image")
    result = Surface((width, height))
    for y in range(height):
        for x in range(width):
            red, green, blue = data[index], data[index + 1], data[index + 2]
            index += 3
            if maximum != 255:
                red, green, blue = red * 255 // maximum, green * 255 // maximum, blue * 255 // maximum
            result._put565(x, y, _color565((red, green, blue)))
    return result


class _Image:
    def load(self, source, namehint=""):
        if hasattr(source, "width") and hasattr(source, "height") and not hasattr(source, "read"):
            return Surface._from_gint_image(source)
        if hasattr(source, "read"):
            data = source.read()
        else:
            handle = open(source, "rb")
            try:
                data = handle.read()
            finally:
                handle.close()
        if data[:2] == b"BM":
            return _load_bmp(data)
        if data[:2] == b"P6":
            return _load_ppm(data)
        raise error("image.load supports uncompressed BMP and binary PPM files")

    def frombuffer(self, buffer, size, format="RGB"):
        return self.fromstring(buffer, size, format)

    def fromstring(self, string, size, format="RGB", flipped=False):
        width, height = map(int, size)
        fmt = format.upper()
        components = 4 if fmt in ("RGBA", "ARGB", "BGRA") else 3
        if len(string) < width * height * components:
            raise ValueError("not enough image data")
        result = Surface((width, height), SRCALPHA if components == 4 else 0)
        for y in range(height):
            target_y = height - 1 - y if flipped else y
            for x in range(width):
                pos = (y * width + x) * components
                values = string[pos:pos + components]
                if fmt.startswith("B"):
                    rgb = (values[2], values[1], values[0])
                else:
                    rgb = (values[0], values[1], values[2])
                result._put565(x, target_y, _color565(rgb))
        return result

    def tostring(self, surface, format="RGB", flipped=False):
        fmt = format.upper()
        output = bytearray()
        rows = range(surface._h - 1, -1, -1) if flipped else range(surface._h)
        for y in rows:
            for x in range(surface._w):
                color = surface.get_at((x, y))
                rgb = (color.b, color.g, color.r) if fmt.startswith("B") else (color.r, color.g, color.b)
                output.extend(rgb)
                if fmt in ("RGBA", "ARGB", "BGRA"):
                    output.append(color.a)
        return bytes(output)

    def get_extended(self):
        return False

    def from_gint(self, gint_image):
        return Surface._from_gint_image(gint_image)


image = _Image()


class _Transform:
    def scale(self, surface, size, dest_surface=None):
        width, height = map(int, size)
        result = dest_surface if dest_surface is not None else Surface((width, height), surface._flags)
        result._colorkey = surface._colorkey
        result._alpha = surface._alpha
        for y in range(height):
            source_y = y * surface._h // height
            for x in range(width):
                source_x = x * surface._w // width
                result._put565(x, y, surface._get565(source_x, source_y))
        return result

    smoothscale = scale

    def scale_by(self, surface, factor, dest_surface=None):
        if isinstance(factor, (tuple, list)):
            width = int(surface._w * factor[0])
            height = int(surface._h * factor[1])
        else:
            width, height = int(surface._w * factor), int(surface._h * factor)
        return self.scale(surface, (max(1, width), max(1, height)), dest_surface)

    def flip(self, surface, flip_x, flip_y):
        result = Surface(surface.get_size(), surface._flags)
        result._colorkey = surface._colorkey
        result._alpha = surface._alpha
        for y in range(surface._h):
            sy = surface._h - 1 - y if flip_y else y
            for x in range(surface._w):
                sx = surface._w - 1 - x if flip_x else x
                result._put565(x, y, surface._get565(sx, sy))
        return result

    def rotate(self, surface, angle):
        radians = _math.radians(angle)
        cosine, sine = _math.cos(radians), _math.sin(radians)
        width = max(1, int(abs(surface._w * cosine) + abs(surface._h * sine)))
        height = max(1, int(abs(surface._w * sine) + abs(surface._h * cosine)))
        result = Surface((width, height), surface._flags)
        result._colorkey = surface._colorkey
        result._alpha = surface._alpha
        if surface._colorkey is not None:
            result.fill(surface._colorkey)
        source_cx, source_cy = (surface._w - 1) / 2, (surface._h - 1) / 2
        target_cx, target_cy = (width - 1) / 2, (height - 1) / 2
        for y in range(height):
            for x in range(width):
                tx, ty = x - target_cx, y - target_cy
                sx = int(tx * cosine + ty * sine + source_cx)
                sy = int(-tx * sine + ty * cosine + source_cy)
                if 0 <= sx < surface._w and 0 <= sy < surface._h:
                    result._put565(x, y, surface._get565(sx, sy))
        return result

    def rotozoom(self, surface, angle, scale):
        rotated = self.rotate(surface, angle)
        return self.scale_by(rotated, scale)


transform = _Transform()


class Sprite:
    def __init__(self, *groups):
        self._groups = []
        if groups:
            self.add(*groups)

    def add(self, *groups):
        for group in groups:
            group.add(self)

    def remove(self, *groups):
        for group in groups:
            group.remove(self)

    def kill(self):
        for group in list(self._groups):
            group.remove(self)

    def alive(self):
        return bool(self._groups)

    def groups(self):
        return list(self._groups)

    def update(self, *args, **kwargs):
        return None


def _flatten_sprites(items):
    for item in items:
        if isinstance(item, (tuple, list, set)):
            for child in _flatten_sprites(item):
                yield child
        elif isinstance(item, Group):
            for child in item.sprites():
                yield child
        else:
            yield item


class Group:
    def __init__(self, *sprites):
        self._sprites = []
        if sprites:
            self.add(*sprites)

    def __len__(self):
        return len(self._sprites)

    def __iter__(self):
        return iter(self._sprites)

    def __contains__(self, sprite):
        return sprite in self._sprites

    def sprites(self):
        return list(self._sprites)

    def add(self, *sprites):
        for item in _flatten_sprites(sprites):
            if item not in self._sprites:
                self._sprites.append(item)
                if not hasattr(item, "_groups"):
                    item._groups = []
                if self not in item._groups:
                    item._groups.append(self)

    def remove(self, *sprites):
        for item in _flatten_sprites(sprites):
            if item in self._sprites:
                self._sprites.remove(item)
                if hasattr(item, "_groups") and self in item._groups:
                    item._groups.remove(self)

    def has(self, *sprites):
        return all(item in self._sprites for item in _flatten_sprites(sprites))

    def copy(self):
        return self.__class__(self._sprites)

    def empty(self):
        self.remove(list(self._sprites))

    def update(self, *args, **kwargs):
        for item in list(self._sprites):
            item.update(*args, **kwargs)

    def draw(self, surface):
        changed = []
        for item in self._sprites:
            if hasattr(item, "image") and hasattr(item, "rect"):
                changed.append(surface.blit(item.image, item.rect))
        return changed


class RenderPlain(Group):
    pass


RenderUpdates = RenderPlain
OrderedUpdates = RenderPlain


class GroupSingle(Group):
    def __init__(self, sprite=None):
        Group.__init__(self)
        if sprite is not None:
            self.add(sprite)

    def add(self, *sprites):
        values = list(_flatten_sprites(sprites))
        if values:
            self.empty()
            Group.add(self, values[-1])

    @property
    def sprite(self):
        return self._sprites[0] if self._sprites else None

    @sprite.setter
    def sprite(self, value):
        self.empty()
        if value is not None:
            Group.add(self, value)


def collide_rect(left, right):
    return left.rect.colliderect(right.rect)


def collide_rect_ratio(ratio):
    def collision(left, right):
        return left.rect.inflate(left.rect.w * (ratio - 1), left.rect.h * (ratio - 1)).colliderect(
            right.rect.inflate(right.rect.w * (ratio - 1), right.rect.h * (ratio - 1)))
    return collision


def spritecollide(sprite, group, dokill, collided=None):
    test = collided or collide_rect
    hits = [other for other in group if test(sprite, other)]
    if dokill:
        for other in hits:
            other.kill()
    return hits


def spritecollideany(sprite, group, collided=None):
    test = collided or collide_rect
    for other in group:
        if test(sprite, other):
            return other
    return None


def groupcollide(groupa, groupb, dokilla, dokillb, collided=None):
    result = {}
    for left in list(groupa):
        hits = spritecollide(left, groupb, dokillb, collided)
        if hits:
            result[left] = hits
            if dokilla:
                left.kill()
    return result


collide_mask = collide_rect


class _SpriteModule:
    Sprite = Sprite
    Group = Group
    GroupSingle = GroupSingle
    RenderPlain = RenderPlain
    RenderUpdates = RenderUpdates
    OrderedUpdates = OrderedUpdates
    collide_rect = staticmethod(collide_rect)
    collide_rect_ratio = staticmethod(collide_rect_ratio)
    collide_mask = staticmethod(collide_mask)
    spritecollide = staticmethod(spritecollide)
    spritecollideany = staticmethod(spritecollideany)
    groupcollide = staticmethod(groupcollide)


sprite = _SpriteModule()


class _Version:
    ver = __version__
    vernum = (0, 1, 0)


version = _Version()


_initialized = False


def init():
    global _initialized
    display.init()
    font.init()
    _initialized = True
    return (2, 0)


def quit():
    global _initialized
    font.quit()
    display.quit()
    _initialized = False


def get_init():
    return _initialized


def get_error():
    return ""


def set_error(message):
    return None


def get_sdl_version(linked=True):
    return (0, 0, 0)
