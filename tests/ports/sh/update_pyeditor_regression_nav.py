"""Keep editor regression aligned with SHIFT+VARS, PyEditorRC turbo, and Files handoff."""

from pathlib import Path

TEST = Path(__file__).with_name("pyeditor_regression.py")
text = TEST.read_text(encoding="utf-8")
changed = False

old_menu = "    assert seen == ['Style', 'Symbols']\n"
new_menu = "    assert seen == ['SHIFT VARS', 'Symbols']\n"
if old_menu in text:
    text = text.replace(old_menu, new_menu, 1)
    changed = True
elif new_menu not in text:
    raise SystemExit("Unable to locate SHIFT VARS regression expectation")

# The original fake key source allowed fewer idle polls than the proven
# PyEditorRC repeat threshold (20) requires. Give the simulated held-key loop
# enough room to reach turbo just as the calculator does.
old_limit = '            assert self.idle_polls < 20, "test exhausted fake key events"\n'
new_limit = '            assert self.idle_polls < 200, "test exhausted fake key events"\n'
if old_limit in text:
    text = text.replace(old_limit, new_limit, 1)
    changed = True
elif new_limit not in text:
    raise SystemExit("Unable to locate fake key idle-poll guard")

old_repeat = '''    # A slow redraw may accumulate many repeats before the release. Drain
    # them before moving, but retain subsequent real typing in exact order.
    g = fake_gint
    reader = editor_module._KeyReader(g)
    g.events[:] = [Event(g.KEYEV_DOWN, g.KEY_RIGHT)] + [
        Event(g.KEYEV_HOLD, g.KEY_RIGHT) for _ in range(30)
    ] + [Event(g.KEYEV_UP, g.KEY_RIGHT), Event(g.KEYEV_DOWN, g.KEY_XOT),
         Event(g.KEYEV_DOWN, g.KEY_LOG)]
    assert [reader.read(), reader.read(), reader.read()] == [g.KEY_RIGHT, g.KEY_XOT, g.KEY_LOG]
    # Repeats while still held are coalesced; the next release stops them.
    g.down.add(g.KEY_RIGHT)
    g.events[:] = [Event(g.KEYEV_HOLD, g.KEY_RIGHT) for _ in range(30)]
    assert reader.read() == g.KEY_RIGHT
    g.events[:] = [Event(g.KEYEV_HOLD, g.KEY_RIGHT), Event(g.KEYEV_UP, g.KEY_RIGHT),
                  Event(g.KEYEV_NONE, 0), Event(g.KEYEV_DOWN, g.KEY_EXIT)]
    assert reader.read() == g.KEY_EXIT
'''
new_repeat = '''    # PyEditorRC turbo: the physical DOWN is returned immediately, then a
    # continuously-held navigation key begins repeating after the original
    # 20-poll threshold and switches the reader into scrolling mode.
    g = fake_gint
    reader = editor_module._KeyReader(g)
    g.down.add(g.KEY_RIGHT)
    g.events[:] = [Event(g.KEYEV_DOWN, g.KEY_RIGHT)]
    assert reader.read(fast_repeat=True) == g.KEY_RIGHT
    assert reader.read(fast_repeat=True) == g.KEY_RIGHT
    assert reader.is_scrolling
    # Releasing a scrolling key deliberately yields one None so the editor can
    # redraw in full-quality mode; the next genuine key-down remains queued.
    g.down.discard(g.KEY_RIGHT)
    g.events[:] = [Event(g.KEYEV_UP, g.KEY_RIGHT), Event(g.KEYEV_DOWN, g.KEY_XOT)]
    assert reader.read(fast_repeat=True) is None
    assert reader.read(fast_repeat=True) == g.KEY_XOT
    assert not reader.is_scrolling
'''
old_repeat_v154 = '''    # PyEditorRC turbo: the physical DOWN is returned immediately, then a
    # continuously-held navigation key begins repeating after the original
    # 20-poll threshold and switches the reader into scrolling mode.
    g = fake_gint
    reader = editor_module._KeyReader(g)
    g.down.add(g.KEY_RIGHT)
    g.events[:] = [Event(g.KEYEV_DOWN, g.KEY_RIGHT)]
    assert reader.read(fast_repeat=True) == g.KEY_RIGHT
    assert reader.read(fast_repeat=True) == g.KEY_RIGHT
    assert reader.is_scrolling
    # Releasing the navigation key stops turbo while preserving the next
    # genuine key-down event in exact order.
    g.down.discard(g.KEY_RIGHT)
    g.events[:] = [Event(g.KEYEV_UP, g.KEY_RIGHT), Event(g.KEYEV_DOWN, g.KEY_XOT)]
    assert reader.read(fast_repeat=True) == g.KEY_XOT
    assert not reader.is_scrolling
'''
if old_repeat in text:
    text = text.replace(old_repeat, new_repeat, 1)
    changed = True
elif old_repeat_v154 in text:
    text = text.replace(old_repeat_v154, new_repeat, 1)
    changed = True
elif new_repeat not in text:
    raise SystemExit("Unable to locate stale key-repeat regression block")

# UI4 intentionally preserves the editor's "run" result only as a terminal
# handoff signal. Files must not execute the script a second time. The old test
# rejected the mere presence of result == "run", which now flags the correct
# handoff implementation as a failure.
old_handoff = '''# Files must not execute an editor-run script for a second time.\npyfiles_source = PYFILES_PATH.read_text(encoding="utf-8")\nassert 'result == "run"' not in pyfiles_source\n'''
new_handoff = '''# Files must not execute an editor-run script for a second time. UI4 may\n# observe the editor's "run" result, but only to leave Files and reveal the\n# shared terminal where the editor already sent the script output.\npyfiles_source = PYFILES_PATH.read_text(encoding="utf-8")\nassert 'result = self.pyeditor.open_file(path, self.theme_name)' in pyfiles_source\nassert 'if result == "run":' in pyfiles_source\nassert 'return "terminal"' in pyfiles_source\nassert 'exec(code, scope, scope)' in pyfiles_source\nassert 'if result == "run":\\n                self.run_file(path)' not in pyfiles_source\n'''
if old_handoff in text:
    text = text.replace(old_handoff, new_handoff, 1)
    changed = True
elif new_handoff not in text:
    raise SystemExit("Unable to locate Files editor-run regression expectation")

if changed:
    TEST.write_text(text, encoding="utf-8")
    print("Updated pyeditor regression for SHIFT VARS, PyEditorRC turbo, and terminal handoff")
else:
    print("pyeditor regression already aligned with SHIFT VARS, PyEditorRC turbo, and terminal handoff")
