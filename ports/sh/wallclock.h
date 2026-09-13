/* PythonUltra calendar and persistent hardware RTC interface. */
#ifndef PYTHONULTRA_WALLCLOCK_H
#define PYTHONULTRA_WALLCLOCK_H

#include <stdbool.h>
#include <stdint.h>

/* Unix epoch, calculator-local civil time; no timezone/DST database. */
#define PE_CLOCK_LAST_SECOND UINT32_C(4102444799) /* 2099-12-31 23:59:59 */

bool pe_clock_valid(int const fields[6]);
uint32_t pe_clock_encode(int const fields[6]);
bool pe_clock_decode(uint32_t seconds, int fields[8]);
bool pe_clock_read(uint32_t *seconds);
bool pe_clock_set(int const fields[6]);

#endif
