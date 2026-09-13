/* Gregorian dates, kept independent of elapsed/game timers. */
#include "wallclock.h"
#include <gint/rtc.h>

static bool leap_year(int year)
{
    return year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
}

static int month_days(int year, int month)
{
    static uint8_t const days[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    return days[month - 1] + (month == 2 && leap_year(year));
}

bool pe_clock_valid(int const f[6])
{
    return f[0] >= 1970 && f[0] <= 2099 && f[1] >= 1 && f[1] <= 12
        && f[2] >= 1 && f[2] <= month_days(f[0], f[1])
        && f[3] >= 0 && f[3] <= 23 && f[4] >= 0 && f[4] <= 59
        && f[5] >= 0 && f[5] <= 59;
}

/* Caller validates first, before accessing month tables or narrowing fields. */
uint32_t pe_clock_encode(int const f[6])
{
    uint32_t days = f[2] - 1;
    for(int year = 1970; year < f[0]; year++)
        days += 365 + leap_year(year);
    for(int month = 1; month < f[1]; month++)
        days += month_days(f[0], month);
    return ((days * 24 + f[3]) * 60 + f[4]) * 60 + f[5];
}

bool pe_clock_decode(uint32_t seconds, int f[8])
{
    if(seconds > PE_CLOCK_LAST_SECOND)
        return false;
    uint32_t days = seconds / 86400;
    f[6] = (days + 3) % 7; /* Monday = 0; 1970-01-01 was Thursday. */
    f[5] = seconds % 60;
    f[4] = (seconds / 60) % 60;
    f[3] = (seconds / 3600) % 24;
    f[0] = 1970;
    while(days >= (uint32_t)(365 + leap_year(f[0]))) {
        days -= 365 + leap_year(f[0]);
        f[0]++;
    }
    f[7] = days + 1;
    f[1] = 1;
    while(days >= (uint32_t)month_days(f[0], f[1])) {
        days -= month_days(f[0], f[1]);
        f[1]++;
    }
    f[2] = days + 1;
    return true;
}

bool pe_clock_read(uint32_t *seconds)
{
    rtc_time_t rtc;
    rtc_get_time(&rtc);
    /* Pinned gint rtc.c passes RMONCNT directly (1..12). Its rtc.h comment
       says 0..11, but the implementation does not apply that conversion. */
    int fields[6] = {rtc.year, rtc.month, rtc.month_day,
        rtc.hours, rtc.minutes, rtc.seconds};
    if(!pe_clock_valid(fields))
        return false;
    *seconds = pe_clock_encode(fields);
    return true;
}

bool pe_clock_set(int const fields[6])
{
    if(!pe_clock_valid(fields))
        return false;
    uint32_t seconds = pe_clock_encode(fields);
    rtc_time_t rtc = {
        .year = fields[0], .month = fields[1], .month_day = fields[2],
        .hours = fields[3], .minutes = fields[4], .seconds = fields[5],
        .week_day = (seconds / 86400 + 4) % 7, /* RTC: Sunday = 0. */
        .ticks = 0,
    };
    /* Writes the battery-backed RTC. No startup restore of a stale saved
       date: elapsed time while the add-in is closed must be preserved. */
    rtc_set_time(&rtc);
    return true;
}
