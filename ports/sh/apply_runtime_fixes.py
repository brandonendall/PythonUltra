"""Apply reproducible PythonUltra source fixes before freezing MicroPython modules.

The fx-CG50 MicroPython port supports indexed bytearray writes but rejects the
CPython-style bytearray slice assignments used by pygame Surface.copy()/fill().
Real-hardware testing also shows that image surfaces must stay at or below
56x56 pixels to avoid large contiguous heap allocations. Apply both fixes before
freezing the pygame package into PythonUltra.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parent
PYGAME = ROOT / "modules" / "pygame" / "__init__.py"


def replace_once(text, old, new, label):
    if new in text:
        return text, False
    if old not in text:
        raise SystemExit("Unable to locate pygame source block: " + label)
    return text.replace(old, new, 1), True


def main():
    text = PYGAME.read_text(encoding="utf-8")
    changed = False

    old_fill = '''        else:\n            pixel = bytes(((color >> 8) & 255, color & 255))\n            row = pixel * area.w\n            for y in range(area.top, area.bottom):\n                start = 2 * (y * self._w + area.left)\n                self._data[start:start + len(row)] = row\n        return area\n'''
    new_fill = '''        else:\n            high = (color >> 8) & 255\n            low = color & 255\n            if area == Rect(0, 0, self._w, self._h):\n                self._data = bytearray(bytes((high, low)) * (self._w * self._h))\n                self._image = _gint.image_rgb565(self._w, self._h, self._data)\n            else:\n                for y in range(area.top, area.bottom):\n                    index = 2 * (y * self._w + area.left)\n                    for _ in range(area.w):\n                        self._data[index] = high\n                        self._data[index + 1] = low\n                        index += 2\n        return area\n'''
    text, did_change = replace_once(text, old_fill, new_fill, "Surface.fill")
    changed = changed or did_change

    old_copy = '''        else:\n            result._data[:] = self._data\n        return result\n'''
    new_copy = '''        else:\n            # CG50 MicroPython rejects bytearray slice assignment. Rebuild the\n            # backing buffer in one allocation, then point the gint image at it.\n            result._data = bytearray(self._data)\n            result._image = _gint.image_rgb565(result._w, result._h, result._data)\n        return result\n'''
    text, did_change = replace_once(text, old_copy, new_copy, "Surface.copy")
    changed = changed or did_change

    old_bmp = '''    if width <= 0 or signed_height == 0 or bpp not in (24, 32) or compression != 0:\n        raise error("BMP must be uncompressed 24-bit or 32-bit")\n    height = abs(signed_height)\n    result = Surface((width, height))\n'''
    new_bmp = '''    if width <= 0 or signed_height == 0 or bpp not in (24, 32) or compression != 0:\n        raise error("BMP must be uncompressed 24-bit or 32-bit")\n    height = abs(signed_height)\n    # Real fx-CG50 heap testing: a full 396x224 RGB565 Surface requests\n    # 177408 contiguous bytes and fails. Keep loadable game images to the\n    # established 56x56 hardware-safe limit and reject larger files before\n    # allocating the Surface backing buffer.\n    if width > 56 or height > 56:\n        raise error("BMP exceeds fx-CG50 56x56 image limit")\n    result = Surface((width, height))\n'''
    text, did_change = replace_once(text, old_bmp, new_bmp, "BMP 56x56 limit")
    changed = changed or did_change

    if changed:
        PYGAME.write_text(text, encoding="utf-8")
        print("Applied fx-CG50 pygame bytearray and 56x56 image-limit fixes")
    else:
        print("fx-CG50 pygame runtime fixes already applied")


if __name__ == "__main__":
    main()
