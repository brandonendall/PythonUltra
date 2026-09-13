PythonUltra Terminal

PythonUltra includes a compact Linux-like terminal command layer for the fx-CG50.
It is intentionally smaller than GNU/Linux but uses the real calculator filesystem
and working directory.

Command help forms:
  help
  help python
  man python
  python -h
  python --help
  COMMAND -h
  COMMAND --help

Python execution:
  python                 Enter the interactive Python REPL
  python file.py         Run a Python file
  python file.py a b     Run with sys.argv = ["file.py", "a", "b"]
  python -c "code"       Execute code directly

Inside the Python REPL, type exit or exit() to return to terminal mode.
