"""Exercise the real C calendar/RTC adapter with a simulated hardware clock.

This checks Gregorian arithmetic and the RTC API boundary, not hardware
persistence or the pinned gint driver's behavior on a physical calculator.
"""
import ctypes
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
RTC_HEADER = """
#include <stdint.h>
typedef struct {
    uint16_t year;
    uint8_t week_day, month, month_day, hours, minutes, seconds, ticks;
} rtc_time_t;
void rtc_get_time(rtc_time_t *time);
void rtc_set_time(rtc_time_t const *time);
"""
RTC_STUB = """
#include <gint/rtc.h>
rtc_time_t hardware;
int writes;
void rtc_get_time(rtc_time_t *time) { *time = hardware; }
void rtc_set_time(rtc_time_t const *time) { hardware = *time; writes++; }
"""

with tempfile.TemporaryDirectory(prefix="pythonultra-clock-") as folder:
    path = Path(folder)
    (path / "gint").mkdir()
    (path / "gint/rtc.h").write_text(RTC_HEADER)
    (path / "rtc.c").write_text(RTC_STUB)
    subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-shared",
                    "-fPIC", "-I" + str(path), str(ROOT / "ports/sh/wallclock.c"),
                    str(path / "rtc.c"), "-o", str(path / "clock.so")], check=True)
    lib = ctypes.CDLL(str(path / "clock.so"))
    ints = ctypes.POINTER(ctypes.c_int)
    lib.pe_clock_valid.argtypes = [ints]
    lib.pe_clock_valid.restype = ctypes.c_bool
    lib.pe_clock_encode.argtypes = [ints]
    lib.pe_clock_encode.restype = ctypes.c_uint32
    lib.pe_clock_decode.argtypes = [ctypes.c_uint32, ints]
    lib.pe_clock_decode.restype = ctypes.c_bool
    lib.pe_clock_set.argtypes = [ints]
    lib.pe_clock_set.restype = ctypes.c_bool
    lib.pe_clock_read.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
    lib.pe_clock_read.restype = ctypes.c_bool
    fields = lambda values: (ctypes.c_int * len(values))(*values)

    date = datetime(1970, 1, 1, tzinfo=timezone.utc)
    end = datetime(2100, 1, 1, tzinfo=timezone.utc)
    days = 0
    while date < end:
        values = date.timetuple()[:6]
        expected = int(date.timestamp())
        assert lib.pe_clock_valid(fields(values))
        assert lib.pe_clock_encode(fields(values)) == expected
        decoded = (ctypes.c_int * 8)()
        assert lib.pe_clock_decode(expected, decoded)
        assert tuple(decoded) == date.timetuple()[:8]
        assert lib.pe_clock_set(fields(values))
        readback = ctypes.c_uint32()
        assert lib.pe_clock_read(ctypes.byref(readback)) and readback.value == expected
        date += timedelta(days=1)
        days += 1

    # Second/minute/day/month/year boundaries, leap day, and the 2038 boundary.
    for values in ((2000, 2, 28, 23, 59, 59), (2024, 2, 29, 23, 59, 59),
                   (2026, 12, 31, 23, 59, 59), (2038, 1, 19, 3, 14, 7),
                   (2099, 12, 31, 23, 59, 58)):
        date = datetime(*values, tzinfo=timezone.utc) + timedelta(seconds=1)
        decoded = (ctypes.c_int * 8)()
        assert lib.pe_clock_decode(lib.pe_clock_encode(fields(values)) + 1, decoded)
        assert tuple(decoded) == date.timetuple()[:8]

    count = ctypes.c_int.in_dll(lib, "writes").value
    for values in ((1969, 1, 1, 0, 0, 0), (2100, 1, 1, 0, 0, 0),
                   (2026, 0, 1, 0, 0, 0), (2026, 13, 1, 0, 0, 0),
                   (2026, 2, 29, 0, 0, 0), (2026, 4, 31, 0, 0, 0),
                   (2026, 1, 0, 0, 0, 0), (2026, 1, 1, 24, 0, 0),
                   (2026, 1, 1, 0, 60, 0), (2026, 1, 1, 0, 0, -1),
                   (2026, 1, 1, 0, 0, 256)):
        assert not lib.pe_clock_valid(fields(values))
        assert not lib.pe_clock_set(fields(values))
    assert ctypes.c_int.in_dll(lib, "writes").value == count
    assert not lib.pe_clock_decode(4102444800, (ctypes.c_int * 8)())

print("PythonUltra native clock: %d dates, rollovers, 2038 and invalid input passed" % days)
