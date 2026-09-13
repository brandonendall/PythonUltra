//---------------------------------------------------------------------------//
//    ____        PythonExtra                                                //
//.-'`_ o `;__,   A community port of MicroPython for CASIO calculators.     //
//.-'` `---`  '   License: MIT (except some files; see LICENSE)              //
//---------------------------------------------------------------------------//

#include "py/mphal.h"
#include "console.h"
#include "py/runtime.h"
#include "wallclock.h"
#include "elapsed.h"
#include "py/mperrno.h"
#include <gint/display.h>
#include <gint/keyboard.h>
#include <unistd.h>

uint64_t pe_monotonic_ms(void)
{
    uint64_t milliseconds;
    if(!pe_elapsed_read(&milliseconds))
        mp_raise_OSError(MP_EBUSY);
    return milliseconds;
}

uint64_t mp_hal_time_ns(void)
{
    uint32_t seconds;
    if(!pe_clock_read(&seconds))
        mp_raise_ValueError(MP_ERROR_TEXT("RTC date invalid; set Date/Time"));
    /* Same epoch as time(); resolution is one second, despite the unit. */
    return (uint64_t)seconds * 1000000000ULL;
}

int mp_hal_stdin_rx_chr(void)
{
    while(1) {
        key_event_t ev = getkey();
        int code_point = console_key_event_to_char(ev);
        if(code_point != 0)
            return code_point;
    }
}

mp_uint_t mp_hal_stdout_tx_strn(const char *str, mp_uint_t len)
{
    int r = write(STDOUT_FILENO, str, len);
    return (r < 0 ? 0 : r);
}
