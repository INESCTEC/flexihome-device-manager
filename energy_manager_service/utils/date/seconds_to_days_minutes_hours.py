import math

from energy_manager_service import generalLogger

seconds_in_day = 60 * 60 * 24
seconds_in_hour = 60 * 60
seconds_in_minute = 60

hours_in_day = 24
minutes_in_hour = 60
seconds_in_minute = 60


def seconds_to_days_minutes_hours(seconds, log=True):
    days = math.floor(seconds / seconds_in_day)
    hours = math.floor(seconds / seconds_in_hour)
    minutes = math.floor(seconds / seconds_in_minute)

    hours_in_rounded_days = days * hours_in_day
    hours_real = hours - hours_in_rounded_days

    minutes_in_rounded_hours = hours * minutes_in_hour
    minutes_real = minutes - minutes_in_rounded_hours

    seconds_in_rounded_minutes = minutes * seconds_in_minute
    seconds_real = seconds - seconds_in_rounded_minutes

    if log:
        generalLogger.info(f"Thread alive for {days} days, {hours_real} hours, {minutes_real} minutes and {seconds_real} seconds.")

    return days, hours_real, minutes_real, seconds_real