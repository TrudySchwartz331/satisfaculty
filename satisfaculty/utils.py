#!/usr/bin/env python3
"""
Utility functions for the scheduling system.
"""


def time_to_minutes(time_str):
    """Convert time string HH:MM to minutes since midnight."""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m


def minutes_to_time(minutes):
    """Convert minutes since midnight to time string HH:MM."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def expand_days(days_str):
    """Expand day codes to individual days. MWF -> [M, W, F], TTH -> [T, TH]."""
    if days_str == "MWF":
        return ['M', 'W', 'F']
    elif days_str == "TTH":
        return ['T', 'TH']
    else:
        # Single day (M, T, W, TH, F)
        return [days_str]


def expand_days_any(days_str):
    """Expand any day combination to individual days. MW -> [M, W], THF -> [TH, F]."""
    days = []
    i = 0
    while i < len(days_str):
        if days_str[i:i + 2] == "TH":
            days.append("TH")
            i += 2
        else:
            days.append(days_str[i])
            i += 1
    return days
