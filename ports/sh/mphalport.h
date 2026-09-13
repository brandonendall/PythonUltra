//---------------------------------------------------------------------------//
//    ____        PythonExtra                                                //
//.-'`_ o `;__,   A community port of MicroPython for CASIO calculators.     //
//.-'` `---`  '   License: MIT (except some files; see LICENSE)              //
//---------------------------------------------------------------------------//
// pe.mphalport: MicroPython's Hardware Abstraction Layer

#include <gint/clock.h>
#include <time.h>
#include "shared/runtime/interrupt_char.h"
#include "py/misc.h"

/* We don't use a VT100 terminal. */
#define MICROPY_HAL_HAS_VT100 (0)
/* Use our custom readline for input(). */
int pe_readline(vstr_t *line, char const *prompt);
#define mp_hal_readline pe_readline

/* Passive sleep. */
static inline void mp_hal_delay_ms(mp_uint_t ms)
{
    sleep_ms(ms);
}
static inline void mp_hal_delay_us(mp_uint_t us)
{
    sleep_us(us);
}

/* Time spent executing. */
uint64_t pe_monotonic_ms(void);
static inline mp_uint_t mp_hal_ticks_ms(void)
{
    return pe_monotonic_ms();
}
static inline mp_uint_t mp_hal_ticks_us(void)
{
    return pe_monotonic_ms() * 1000;
}
static inline mp_uint_t mp_hal_ticks_cpu(void)
{
    return pe_monotonic_ms();
}

/* Time since Epoch in nanoseconds. */
uint64_t mp_hal_time_ns(void);
