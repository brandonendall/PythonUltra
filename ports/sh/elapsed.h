/* Active-add-in elapsed time, independent of the RTC date and time. */
#ifndef PYTHONULTRA_ELAPSED_H
#define PYTHONULTRA_ELAPSED_H
#include <stdbool.h>
#include <stdint.h>
bool pe_elapsed_read(uint64_t *milliseconds);
#endif
