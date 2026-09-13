"""Use the supplied 92x64 PythonUltra icon unchanged in every build variant."""
from pathlib import Path
from shutil import copyfile
from PIL import Image

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "logo/pythonultra-icon-92x64.png"


def main():
    with Image.open(SOURCE) as image:
        if image.size != (92, 64) or image.mode != "RGB":
            raise SystemExit("Expected supplied 92x64 RGB icon")
        if any(image.getpixel(xy) != (0, 0, 0)
               for xy in ((0, 0), (91, 0), (0, 63), (91, 63))):
            raise SystemExit("Expected black icon corners")
    for name in ("icon-uns.png", "icon-sel.png", "icon-uns-dev.png", "icon-sel-dev.png"):
        copyfile(SOURCE, HERE / name)
    print("Prepared supplied PythonUltra icon (unchanged)")


if __name__ == "__main__":
    main()
