"""Calculator clock editor. Only Save writes the native hardware RTC."""

_LABELS = ("Year", "Month", "Day", "Hour", "Minute", "Second")


def validate(fields):
    if len(fields) != 6 or any(not isinstance(v, int) for v in fields):
        raise ValueError("Enter six whole numbers")
    year, month, day, hour, minute, second = fields
    if not 1970 <= year <= 2099:
        raise ValueError("Year must be 1970 to 2099")
    if not 1 <= month <= 12:
        raise ValueError("Month must be 1 to 12")
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[month - 1]
    if not 1 <= day <= days:
        raise ValueError("Day must be 1 to %d" % days)
    if not 0 <= hour <= 23:
        raise ValueError("Hour must be 0 to 23")
    if not 0 <= minute <= 59 or not 0 <= second <= 59:
        raise ValueError("Minute/second must be 0 to 59")
    return tuple(fields)


def clock_text():
    import time
    try:
        fields = validate(time.localtime()[:6])
        return "%04d-%02d-%02d %02d:%02d:%02d" % fields
    except (AttributeError, ValueError, OSError, OverflowError):
        return "Unavailable - set Date/Time"


def save(fields):
    import time
    fields = validate(fields)
    if not hasattr(time, "set_datetime"):
        raise OSError("Clock setting needs a newer build")
    time.set_datetime(fields)
    # Read back the hardware. A second may roll over during the write/read.
    delta = time.mktime(time.localtime()) - time.mktime(fields + (0, 0))
    if not 0 <= delta <= 1:
        raise OSError("Clock readback failed; check time")


def show(dark=False):
    import gint as g
    try:
        g.dfont_builtin("small")
        return _show(g, dark)
    finally:
        g.dfont(None)


def _show(g, dark):
    import time
    from pythonultra import menu_border, _popup_text
    try:
        fields = list(validate(time.localtime()[:6]))
    except (AttributeError, ValueError, OSError, OverflowError):
        # An editable starting value only; never written without Save.
        fields = [2000, 1, 1, 0, 0, 0]
    selected, digits, message = 0, "", "Set calculator-local date/time"
    bg, fg = (0x0000, 0xFFFF) if dark else (0xFFFF, 0x0000)
    accent = menu_border()
    keys = tuple(getattr(g, "KEY_" + str(n)) for n in range(10))
    g.clearevents()
    while True:
        g.drect(0, 0, 395, 223, bg)
        g.drect_border(24, 24, 372, 204, bg, 2, accent)
        g.dtext(38, 30, fg, "Date / Time")
        g.dtext(38, 46, fg, _popup_text(g, clock_text(), 319))
        for i, label in enumerate(_LABELS):
            y = 64 + i * 18
            if i == selected:
                g.drect_border(34, y - 2, 358, y + 13, bg, 1, accent)
            g.dtext(44, y, fg, label)
            value = digits if i == selected and digits else str(fields[i])
            g.dtext(205, y, fg, value)
        g.dtext(38, 180, fg, _popup_text(g, message, 319))
        g.dtext(24, 213, fg, "F1 Save   +/- Adjust   EXIT Cancel")
        g.dupdate()
        ev = g.pollevent()
        if ev.type != g.KEYEV_DOWN and not (ev.type == g.KEYEV_HOLD
                and ev.key in (g.KEY_UP, g.KEY_DOWN, g.KEY_ADD, g.KEY_SUB)):
            time.sleep_ms(50)
            continue
        key = ev.key
        if key == g.KEY_EXIT:
            return False
        if key in keys:
            limit = 4 if selected == 0 else 2
            digits = (digits + str(keys.index(key)))[-limit:]
            fields[selected] = int(digits)
        elif key in (g.KEY_UP, g.KEY_DOWN, g.KEY_EXE):
            selected = (selected + (-1 if key == g.KEY_UP else 1)) % 6
            digits = ""
        elif key in (g.KEY_ADD, g.KEY_SUB):
            fields[selected] += 1 if key == g.KEY_ADD else -1
            digits = ""
        elif key == g.KEY_F1:
            try:
                save(fields)
                return True
            except (ValueError, OSError, OverflowError) as exc:
                message = str(exc)
