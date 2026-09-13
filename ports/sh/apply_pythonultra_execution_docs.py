"""Document prepared C-file execution and keep browser handoffs out of output."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = {
    "pyfiles": {
        "browse": "Open Files at folder with theme; return None after exit or execution. Select a .c file and press EXE to run main() through PicoC and keep its output in the terminal.",
        "Browser.enter_selected": "Enter a directory, run a selected .c file, or open information for another file. Return the internal terminal marker after C execution.",
        "Browser.run_file": "Run a .py or .c file after a read-permission check. C files call main() and print an exit code. Return the internal terminal marker after success or reported errors; restore sys.path and collect garbage.",
        "Browser.file_info": "Show file details and actions; F4 runs Python or C source and hands execution output back to the terminal.",
        "Browser.run": "Handle Files navigation and actions until exit or an internal terminal handoff is requested.",
    },
    "pyeditor": {
        "Editor.draw_line_turbo": "Draw one editor line without syntax coloring while accelerated held-key navigation is active.",
    },
}


def document(path, docs):
    """Insert or replace exact module/class function docstrings using AST locations."""
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    found = set()
    edits = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        owner = next((parent.name for parent in tree.body
                      if isinstance(parent, ast.ClassDef) and node in parent.body), None)
        key = (owner + "." if owner else "") + node.name
        if key not in docs:
            continue
        found.add(key)
        first = node.body[0]
        start = first.lineno - 1
        end = first.end_lineno if ast.get_docstring(node) is not None else start
        line = " " * first.col_offset + '"""' + docs[key] + '"""\n'
        edits.append((start, end, line))
    if found != set(docs):
        raise SystemExit("Missing documented functions: " + repr(set(docs) - found))
    for start, end, line in sorted(edits, reverse=True):
        lines[start:end] = [line]
    text = "".join(lines)
    if path.parent.name == "pyfiles":
        text = text.replace('    return Browser(folder, theme).run()',
                            '    Browser(folder, theme).run()')
    path.write_text(text, encoding="utf-8")


def main():
    """Apply documentation after all feature transformations have completed."""
    for module, docs in DOCS.items():
        document(ROOT / "modules" / module / "__init__.py", docs)
    print("PythonUltra execution docstrings and quiet browser return: ready")


if __name__ == "__main__":
    main()
