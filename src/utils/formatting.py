import pandas as pd
import numpy as np
from typing import Union, Optional

def format_minutes_to_dhm(minutes: Union[float, int, None]) -> str:
    """
    Converts duration in minutes into a clean 'Xd Yh Zm' string format.
    Examples:
        45      -> "45m"
        135     -> "2h 15m"
        1500    -> "1d 1h 0m"
        18535.7 -> "12d 20h 56m"
        0       -> "0m"
        None    -> "—"
    """
    if minutes is None or pd.isna(minutes):
        return "—"
    
    try:
        total_mins = int(round(float(minutes)))
    except (ValueError, TypeError):
        return "—"
    
    if total_mins < 0:
        return "0m"
    if total_mins == 0:
        return "0m"
    
    days = total_mins // (24 * 60)
    rem_mins = total_mins % (24 * 60)
    hours = rem_mins // 60
    mins = rem_mins % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m")
    
    return " ".join(parts)

def format_hours_to_dhm(hours: Union[float, int, None]) -> str:
    """
    Converts duration in hours into a clean 'Xd Yh Zm' string format.
    Examples:
        0.5      -> "30m"
        11.42    -> "11h 25m"
        38.5     -> "1d 14h 30m"
        138373.7 -> "5765d 13h 42m"
        None     -> "—"
    """
    if hours is None or pd.isna(hours):
        return "—"
    try:
        minutes = float(hours) * 60.0
        return format_minutes_to_dhm(minutes)
    except (ValueError, TypeError):
        return "—"

def format_delay_chip(delay_mins: Union[float, int, None], is_in_progress: bool = False) -> str:
    """
    Formats a delay value for table chips and cards.
    """
    if delay_mins is None or pd.isna(delay_mins):
        return "—"
    formatted = format_minutes_to_dhm(delay_mins)
    if is_in_progress:
        return f"In Progress ({formatted})"
    return formatted
