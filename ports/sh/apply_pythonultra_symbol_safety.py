'''Make every user-inserted editor punctuation character QSTR-safe.

Frozen one-character punctuation strings can surface on fx-CG50 hardware as
MicroPython's internal QSTR spellings (for example __dot__).  Construct all
punctuation returned by the physical editor key maps at runtime from ASCII
codes, just like the programming-symbol pickers already do.
'''

from pathlib import Path

ROOT = Path(__file__).resolve().parent
EDITOR = ROOT / "modules" / "pyeditor" / "__init__.py"
MARKER = "EDITOR_SYMBOL_SAFETY_VERSION = 1"


def main():
    text = EDITOR.read_text(encoding="utf-8")
    if MARKER in text:
        print("PythonUltra editor symbol safety already applied")
        return

    marker = "EDITOR_FIXES_VERSION = 1\n"
    if marker not in text:
        raise SystemExit("Unable to locate editor version marker")
    text = text.replace(marker, marker + MARKER + "\n", 1)

    start = text.index("def _maps(g):\n")
    end = text.index("\n\nclass Editor:", start)
    replacement = '''def _maps(g):
    # Do not freeze punctuation as one-character strings. On calculator
    # hardware MicroPython QSTR spellings such as __dot__ can otherwise leak
    # into the editor. Runtime chr() keeps the actual ASCII character.
    c = chr
    base = {
        g.KEY_0:"0", g.KEY_1:"1", g.KEY_2:"2", g.KEY_3:"3", g.KEY_4:"4",
        g.KEY_5:"5", g.KEY_6:"6", g.KEY_7:"7", g.KEY_8:"8", g.KEY_9:"9",
        g.KEY_DOT:c(46), g.KEY_ADD:c(43), g.KEY_SUB:c(45), g.KEY_MUL:c(42),
        g.KEY_DIV:c(47), g.KEY_LEFTPAR:c(40), g.KEY_RIGHTPAR:c(41),
        g.KEY_COMMA:c(44), g.KEY_NEG:c(32), g.KEY_EQUALS:c(61),
    }
    alpha = {
        g.KEY_XOT:"a", g.KEY_LOG:"b", g.KEY_LN:"c", g.KEY_SIN:"d",
        g.KEY_COS:"e", g.KEY_TAN:"f", g.KEY_FRAC:"g", g.KEY_FD:"h",
        g.KEY_LEFTPAR:"i", g.KEY_RIGHTPAR:"j", g.KEY_COMMA:"k", g.KEY_ARROW:"l",
        g.KEY_7:"m", g.KEY_8:"n", g.KEY_9:"o", g.KEY_4:"p", g.KEY_5:"q",
        g.KEY_6:"r", g.KEY_MUL:"s", g.KEY_DIV:"t", g.KEY_1:"u", g.KEY_2:"v",
        g.KEY_3:"w", g.KEY_ADD:"x", g.KEY_SUB:"y", g.KEY_0:"z",
        g.KEY_DOT:c(32), g.KEY_EXP:c(34), g.KEY_VARS:c(95), g.KEY_NEG:c(32),
    }
    shift = {
        g.KEY_MUL:c(123), g.KEY_DIV:c(125), g.KEY_ADD:c(91), g.KEY_SUB:c(93),
        g.KEY_DOT:c(61), g.KEY_0:c(58),
        g.KEY_EXP:"3" + c(46) + "14159",
    }
    return base, alpha, shift
'''
    text = text[:start] + replacement + text[end:]
    EDITOR.write_text(text, encoding="utf-8")
    print("Applied PythonUltra all-symbol editor safety")


if __name__ == "__main__":
    main()
