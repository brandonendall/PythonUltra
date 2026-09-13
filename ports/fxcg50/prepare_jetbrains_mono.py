"""Generate fxconv font sheets for JetBrains Mono.

The source font is fetched from a pinned revision of the official
JetBrains/JetBrainsMono repository. The generated PNGs are build artifacts;
we intentionally do not vendor or expose the TTF itself.

JetBrains Mono is licensed under the SIL Open Font License 1.1. A copy of the
license is kept beside this script as JetBrainsMono-OFL.txt.
"""

from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
JETBRAINS_COMMIT = "19371302b95d218af43299bce79ddbddd0bc364d"
FONT_URL = (
    "https://raw.githubusercontent.com/JetBrains/JetBrainsMono/"
    + JETBRAINS_COMMIT
    + "/fonts/ttf/JetBrainsMono-Regular.ttf"
)

# Match the three calculator font sizes already used by PythonExtra/casioplot.
SHEETS = (
    ("font_jb_9.png", 9, 10),
    ("font_jb_13.png", 12, 17),
    ("font_jb_19.png", 18, 23),
)


def _font_for_cell(data, cell_w, cell_h):
    """Choose the largest readable JetBrains Mono size that fits the cell."""
    for px in range(cell_h + 2, 3, -1):
        font = ImageFont.truetype(BytesIO(data), px)
        ascent, descent = font.getmetrics()
        width = font.getlength("M")
        if ascent + descent <= cell_h and width <= cell_w - 1:
            return font, ascent, descent
    raise RuntimeError("Unable to fit JetBrains Mono into %dx%d" % (cell_w, cell_h))


def _render_sheet(data, filename, cell_w, cell_h):
    # fxconv's `charset: print` grid is 16 columns x 6 rows. Printable ASCII
    # occupies U+0020..U+007E; the final cell is deliberately left blank.
    image = Image.new("L", (cell_w * 16, cell_h * 6), 255)
    draw = ImageDraw.Draw(image)
    font, ascent, descent = _font_for_cell(data, cell_w, cell_h)
    baseline_offset = (cell_h + ascent - descent) // 2

    for codepoint in range(32, 127):
        index = codepoint - 32
        col = index % 16
        row = index // 16
        x0 = col * cell_w
        y0 = row * cell_h
        ch = chr(codepoint)
        advance = font.getlength(ch)
        x = x0 + (cell_w - advance) / 2
        baseline = y0 + baseline_offset
        draw.text((x, baseline), ch, font=font, fill=0, anchor="ls")

    out = ROOT / filename
    image.save(out, "PNG", optimize=True)
    print("generated", out.name, "%dx%d" % image.size, "font px", font.size)


def main():
    print("Fetching JetBrains Mono from pinned commit", JETBRAINS_COMMIT)
    with urlopen(FONT_URL, timeout=30) as response:
        data = response.read()
    if len(data) < 100000:
        raise RuntimeError("JetBrains Mono download is unexpectedly small")
    for filename, cell_w, cell_h in SHEETS:
        _render_sheet(data, filename, cell_w, cell_h)


if __name__ == "__main__":
    main()
