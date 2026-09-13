'''Add documentation strings to the runtime-added editor navigation API.'''

from pathlib import Path

EDITOR = Path(__file__).resolve().parent / "modules" / "pyeditor" / "__init__.py"

DOCS = {
    "jump_top": "Move the editor cursor and viewport to the first line and first column.",
    "jump_bottom": "Move the editor cursor and viewport to the end of the final line.",
    "jump_line": "Prompt for a 1-based line number, clamp it to the buffer, and jump there.",
    "vars_menu": "Open the SHIFT+VARS editor menu containing style and jump commands.",
}


def main():
    text = EDITOR.read_text(encoding="utf-8")
    changed = False
    for name, doc in DOCS.items():
        needle = "    def " + name + "(self):\n"
        replacement = needle + '        """' + doc + '"""\n'
        if replacement in text:
            continue
        if needle not in text:
            raise SystemExit("Missing editor navigation method: " + name)
        text = text.replace(needle, replacement, 1)
        changed = True
    if changed:
        EDITOR.write_text(text, encoding="utf-8")
    print("PythonUltra editor navigation docs: " + ("applied" if changed else "already applied"))


if __name__ == "__main__":
    main()
