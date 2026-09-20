"""Utility functions for calendar operations"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from dateutil import parser
from zoneinfo import ZoneInfo
from tools.shared.logging import setup_tool_logger

logger = setup_tool_logger(__name__)

def parse_datetime_string(date_str: str, user_timezone: str = 'UTC') -> datetime:
    """
    Parse natural language date/time strings with proper timezone handling.
    
    Supports:
    - "tomorrow at 2pm"
    - "today at 3pm"
    - "next Monday at 10am"
    - "Saturday at 2pm" (finds next Saturday)
    - "Saturday" (finds next Saturday at 9am)
    - ISO format dates
    - Relative dates
    
    Args:
        date_str: Natural language or ISO date string
        user_timezone: User's timezone (default: UTC)
        
    Returns:
        Parsed datetime object in user's timezone
    """
    try:
        tz = ZoneInfo(user_timezone)
    except Exception:
        tz = ZoneInfo('UTC')
    
    now = datetime.now(tz)
    date_str_lower = date_str.lower().strip()
    
    # Days of week mapping
    days_of_week = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    try:
        # Handle relative dates
        if 'tomorrow' in date_str_lower:
            if any(time_word in date_str_lower for time_word in ['am', 'pm', ':', 'at']):
                time_part = date_str_lower.replace('tomorrow', '').strip()
                tomorrow = now + timedelta(days=1)
                parsed = parser.parse(time_part, default=tomorrow)
            else:
                tomorrow = now + timedelta(days=1)
                parsed = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        elif 'today' in date_str_lower:
            if any(time_word in date_str_lower for time_word in ['am', 'pm', ':', 'at']):
                time_part = date_str_lower.replace('today', '').strip()
                parsed = parser.parse(time_part, default=now)
            else:
                parsed = now + timedelta(hours=1)
        elif 'next week' in date_str_lower:
            parsed = parser.parse(date_str_lower, default=now + timedelta(days=7))
        elif 'next' in date_str_lower:
            # Handle "next [day of week]"
            target_day = None
            for day_name, day_num in days_of_week.items():
                if day_name in date_str_lower:
                    target_day = day_num
                    break
            
            if target_day is not None:
                now_date_only = now.replace(hour=0, minute=0, second=0, microsecond=0)
                current_day = now_date_only.weekday()
                days_ahead = target_day - current_day
                
                if days_ahead <= 0:
                    days_ahead += 7
                
                target_date = now_date_only + timedelta(days=days_ahead)
                
                if any(time_word in date_str_lower for time_word in ['am', 'pm', ':', 'at']):
                    time_part = date_str_lower.replace('next', '').strip()
                    for day_name in days_of_week.keys():
                        time_part = time_part.replace(day_name, '').strip()
                    
                    if time_part:
                        try:
                            time_parsed = parser.parse(time_part, default=target_date)
                            parsed = time_parsed
                        except Exception:
                            parsed = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                    else:
                        parsed = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                else:
                    parsed = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                parsed = parser.parse(date_str, default=now + timedelta(days=7))
        else:
            # Check if it's a standalone day name (without "next")
            target_day = None
            for day_name, day_num in days_of_week.items():
                # Check if the day name appears in the string
                if day_name in date_str_lower:
                    # Make sure it's not part of another word (e.g., "saturday" not "saturdays")
                    # Simple check: day name should be at word boundary or standalone
                    day_index = date_str_lower.find(day_name)
                    if day_index >= 0:
                        # Check if it's a complete word (before/after are not letters)
                        before_char = date_str_lower[day_index - 1] if day_index > 0 else ' '
                        after_char = date_str_lower[day_index + len(day_name)] if day_index + len(day_name) < len(date_str_lower) else ' '
                        if not before_char.isalpha() and not after_char.isalpha():
                            target_day = day_num
                            break
            
            if target_day is not None:
                # Found a standalone day name - find next occurrence
                now_date_only = now.replace(hour=0, minute=0, second=0, microsecond=0)
                current_day = now_date_only.weekday()
                days_ahead = target_day - current_day
                
                # If the day is today or has passed, get next week's occurrence
                if days_ahead <= 0:
                    days_ahead += 7
                
                target_date = now_date_only + timedelta(days=days_ahead)
                
                # Extract time if present
                if any(time_word in date_str_lower for time_word in ['am', 'pm', ':', 'at']):
                    # Remove the day name and parse time
                    time_part = date_str_lower
                    for day_name in days_of_week.keys():
                        time_part = time_part.replace(day_name, '').strip()
                    
                    if time_part:
                        try:
                            time_parsed = parser.parse(time_part, default=target_date)
                            parsed = time_parsed
                        except Exception:
                            parsed = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                    else:
                        parsed = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                else:
                    # No time specified, default to 9am
                    parsed = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                # Not a day name, try generic parser
                parsed = parser.parse(date_str, default=now)
        
        # Ensure timezone-aware
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tz)
        else:
            parsed = parsed.astimezone(tz)
        
        return parsed
        
    except Exception as e:
        logger.warning(f"Failed to parse date string '{date_str}': {e}")
        return now + timedelta(hours=1)

def parse_duration_string(duration_str: str) -> timedelta:
    """
    Parse duration strings like '1 hour', '30 minutes'.
    
    Args:
        duration_str: Duration string
        
    Returns:
        timedelta object
    """
    duration_str = duration_str.lower().strip()
    
    if 'hour' in duration_str or 'hr' in duration_str:
        hours = float(''.join(filter(str.isdigit, duration_str.split()[0])))
        return timedelta(hours=hours)
    elif 'minute' in duration_str or 'min' in duration_str:
        minutes = float(''.join(filter(str.isdigit, duration_str.split()[0])))
        return timedelta(minutes=minutes)
    else:
        return timedelta(hours=1)  # Default to 1 hour