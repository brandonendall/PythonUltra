"""Turn the connected outer background of generated PythonUltra icons black."""

from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
NAMES = ("icon-uns.png", "icon-sel.png", "icon-uns-dev.png", "icon-sel-dev.png")

for name in NAMES:
    path = HERE / name
    image = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(image)
    # The workflow letterboxes the logo with one connected corner color.
    # Flood from every corner so only the outer app-icon background changes.
    for xy in ((0, 0), (image.width - 1, 0), (0, image.height - 1),
               (image.width - 1, image.height - 1)):
        ImageDraw.floodfill(image, xy, (0, 0, 0), thresh=10)
    image.save(path, "PNG")
    print("Black icon background:", path)
