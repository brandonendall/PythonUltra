"""Make the PythonUltra information view a plain, unnumbered list.

Catalog and other selection menus keep their numeric shortcuts. The F6/info
screen is informational only, so it should not imply that its lines are
selectable commands.
"""
from pathlib import Path

PATH = Path(__file__).resolve().parent / "modules" / "pythonultra" / "__init__.py"
text = PATH.read_text(encoding="utf-8")

replacements = (
    (
        "def popup(title, items, dark=False):\n    \"\"\"Use a bounded menu font, independent of the terminal/editor size.\"\"\"\n    import gint\n    try:\n        return _popup(title, items, dark)\n",
        "def popup(title, items, dark=False, numbered=True):\n    \"\"\"Use a bounded menu font, independent of the terminal/editor size.\"\"\"\n    import gint\n    try:\n        return _popup(title, items, dark, numbered)\n",
    ),
    (
        "def _popup(title, items, dark=False):\n    \"\"\"Display a Geometry-style modal list and return the chosen item.\"\"\"\n",
        "def _popup(title, items, dark=False, numbered=True):\n    \"\"\"Display a Geometry-style modal list and return the chosen item.\"\"\"\n",
    ),
    (
        "            prefix = str(row + 1) if row < 9 else \"0\"\n            gint.dtext(panel_x + 14, y + 1, fg,\n                       _popup_text(gint, prefix + \":\" + str(items[idx]),\n                                   panel_right - panel_x - 30))\n",
        "            prefix = (str(row + 1) if row < 9 else \"0\") + \":\" if numbered else \"\"\n            gint.dtext(panel_x + 14, y + 1, fg,\n                       _popup_text(gint, prefix + str(items[idx]),\n                                   panel_right - panel_x - 30))\n",
    ),
    (
        "        number_keys = (\n            gint.KEY_1, gint.KEY_2, gint.KEY_3, gint.KEY_4, gint.KEY_5,\n            gint.KEY_6, gint.KEY_7, gint.KEY_8, gint.KEY_9, gint.KEY_0,\n        )\n        for row, number_key in enumerate(number_keys):\n            if key == number_key:\n                idx = scroll + row\n                if idx < len(items):\n                    return items[idx]\n",
        "        if numbered:\n            number_keys = (\n                gint.KEY_1, gint.KEY_2, gint.KEY_3, gint.KEY_4, gint.KEY_5,\n                gint.KEY_6, gint.KEY_7, gint.KEY_8, gint.KEY_9, gint.KEY_0,\n            )\n            for row, number_key in enumerate(number_keys):\n                if key == number_key:\n                    idx = scroll + row\n                    if idx < len(items):\n                        return items[idx]\n",
    ),
    (
        "def info_ui(dark=False):\n    return popup(\"PythonUltra Info\", info_lines(), dark)\n",
        "def info_ui(dark=False):\n    return popup(\"PythonUltra Info\", info_lines(), dark, numbered=False)\n",
    ),
)

changed = False
for old, new in replacements:
    if old.startswith("def info_ui(") and 'return information_panel("PythonUltra Info", info_lines(), dark)' in text:
        # PythonUltra retains its custom dark, framed informational panel.
        # Apply the unnumbered behavior to its light-mode popup fallback.
        old = 'return popup(title, lines, False)'
        new = 'return popup(title, lines, False, numbered=False)'
    if new in text:
        continue
    if old not in text:
        raise SystemExit("PythonUltra info-menu patch target not found")
    text = text.replace(old, new, 1)
    changed = True

if changed:
    PATH.write_text(text, encoding="utf-8")
    print("PythonUltra info menu: unnumbered informational view applied")
else:
    print("PythonUltra info menu: already applied")
