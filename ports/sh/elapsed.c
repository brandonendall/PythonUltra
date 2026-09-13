#include "elapsed.h"
#include <gint/timer.h>
#include <gint/cpu.h>

static volatile uint64_t elapsed_ms;
static int elapsed_timer = -1;

static int elapsed_tick(void)
{
    elapsed_ms++;
    return TIMER_CONTINUE;
}

bool pe_elapsed_read(uint64_t *milliseconds)
{
    if(elapsed_timer < 0) {
        /* A TMU provides the precision needed for a 1 ms period. Reserving
           it once avoids the RTC-backed fxlibc clock(), including midnight
           wrap and jumps caused by setting the calendar. */
        elapsed_timer = timer_configure(TIMER_TMU, 1000, GINT_CALL(elapsed_tick));
        if(elapsed_timer < 0)
            return false;
        timer_start(elapsed_timer);
    }
    /* The SH processor is 32-bit; do not tear a 64-bit ISR counter read. */
    cpu_atomic_start();
    *milliseconds = elapsed_ms;
    cpu_atomic_end();
    return true;
}

__attribute__((destructor))
static void elapsed_stop(void)
{
    if(elapsed_timer >= 0)
        timer_stop(elapsed_timer);
}
