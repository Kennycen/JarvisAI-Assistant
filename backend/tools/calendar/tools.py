"""Google Calendar function tools for LiveKit agent"""
from typing import Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import Field
from livekit.agents import function_tool, RunContext
from tools.calendar.manager import GoogleCalendarManager
from tools.calendar.utils import parse_datetime_string, parse_duration_string
from tools.shared.context import get_room_name
from tools.shared.database import get_user_id_from_room
from tools.shared.errors import AuthenticationError, APIError
from tools.shared.logging import setup_tool_logger

logger = setup_tool_logger(__name__)

def _get_calendar_manager(context: RunContext) -> GoogleCalendarManager:
    """Helper to get calendar manager from context"""
    room_name = get_room_name(context)
    user_id = get_user_id_from_room(room_name) if room_name else None
    
    if not user_id and not room_name:
        logger.warning("Could not determine user from context")
    
    return GoogleCalendarManager(user_id=user_id)

@function_tool()
async def add_calendar_event_google(
    context: RunContext,
    title: str,
    date_time: str,
    duration: str = "1 hour",
    description: Optional[str] = Field(default=None),  # Use Field
    location: Optional[str] = Field(default=None),    # Use Field
    attendees: Optional[str] = Field(default=None)     # Use Field   
) -> str:
    """
    Add a new event to Google Calendar.
    
    TRIGGER WORDS: schedule, add meeting, book appointment, create event,
    set up meeting, add to calendar
    
    Args:
        context: LiveKit agent context (automatically provided)
        title: Event title/name (required)
        date_time: Date and time (e.g., "tomorrow 2pm", "2024-01-15 14:30")
        duration: Event duration (default: "1 hour")
        description: Event description (optional)
        location: Event location (optional)
        attendees: Comma-separated email addresses (optional)
    
    Returns:
        Success message with event details
    """
    try:
        logger.info(f"Adding calendar event: {title} at {date_time}")
        
        manager = _get_calendar_manager(context)
        
        # Parse date and duration
        parsed_datetime = parse_datetime_string(date_time, manager.timezone)
        parsed_duration = parse_duration_string(duration)
        end_time = parsed_datetime + parsed_duration
        
        # Build event data
        event_data = {
            'summary': title,
            'start': {
                'dateTime': parsed_datetime.isoformat(),
                'timeZone': manager.timezone,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': manager.timezone,
            },
        }
        
        # Add optional fields
        if description and description.strip():
            event_data['description'] = description
        if location and location.strip():
            event_data['location'] = location
        
        # Handle attendees
        if attendees and attendees.strip():
            attendee_list = [
                email.strip() for email in attendees.split(',')
                if email.strip() and '@' in email
            ]
            if attendee_list:
                event_data['attendees'] = [{'email': email} for email in attendee_list]
        
        # Create event
        manager.create_event(event_data)
        
        formatted_time = parsed_datetime.strftime('%B %d, %Y at %I:%M %p')
        return f"Event '{title}' scheduled for {formatted_time}, Sir. Duration: {duration}."
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        return f"Calendar not connected. Please connect your Google Calendar account, Sir."
    except APIError as e:
        logger.error(f"API error: {e}")
        return f"Failed to create calendar event: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return f"An error occurred while creating the event: {str(e)}"

@function_tool()
async def view_calendar_events_google(
    context: RunContext,
    date: Optional[str] = None,
    max_results: int = 10
) -> str:
    """
    View events from Google Calendar for a specific date or date range.
    
    TRIGGER WORDS: show calendar, what's on schedule, check calendar,
    view events, what's today, next week, this week
    
    Args:
        context: LiveKit agent context
        date: Date or range (e.g., "today", "tomorrow", "next week")
        max_results: Maximum number of events (default: 10)
    
    Returns:
        Formatted string describing the events
    """
    try:
        logger.info(f"Viewing calendar events for: {date or 'today'}")
        
        manager = _get_calendar_manager(context)
        user_tz = ZoneInfo(manager.timezone)
        
        # Parse date
        date_lower = (date or "").lower().strip()
        
        if date:
            target_date = parse_datetime_string(date, manager.timezone)
            target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            target_date = datetime.now(user_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Determine time range
        if 'next week' in date_lower:
            current_day = target_date.weekday()
            days_ahead = 7 - current_day
            if days_ahead == 0:
                days_ahead = 7
            time_min = target_date + timedelta(days=days_ahead)
            time_max = time_min + timedelta(days=7)
            range_description = f"next week (starting {time_min.strftime('%B %d')})"
        elif 'this week' in date_lower:
            days_back = target_date.weekday()
            time_min = target_date - timedelta(days=days_back)
            time_max = time_min + timedelta(days=7)
            range_description = f"this week (starting {time_min.strftime('%B %d')})"
        else:
            time_min = target_date
            time_max = time_min + timedelta(days=1)
            range_description = target_date.strftime('%B %d, %Y')
        
        # Convert to UTC for API
        time_min_utc = time_min.astimezone(ZoneInfo('UTC'))
        time_max_utc = time_max.astimezone(ZoneInfo('UTC'))
        
        # Get events
        events = manager.get_events(time_min_utc, time_max_utc, max_results)
        
        if not events:
            return f"No events found for {range_description}, Sir."
        
        # Format events
        event_list = []
        is_range = 'week' in date_lower
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            title = event.get('summary', 'No Title')
            
            if 'T' in start:
                if start.endswith('Z'):
                    start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                else:
                    start_time = datetime.fromisoformat(start)
                
                if start_time.tzinfo:
                    start_time = start_time.astimezone(user_tz)
                
                if is_range:
                    formatted_time = start_time.strftime('%B %d at %I:%M %p')
                else:
                    formatted_time = start_time.strftime('%I:%M %p')
                
                event_list.append(f"{formatted_time} - {title}")
            else:
                event_list.append(f"All day - {title}")
        
        # Create response
        if len(events) == 1:
            return f"You have one event {range_description}, Sir: {event_list[0]}"
        else:
            events_text = ", ".join(event_list)
            return f"You have {len(events)} events {range_description}, Sir: {events_text}"
        
    except AuthenticationError as e:
        return f"Calendar not connected, Sir."
    except APIError as e:
        return f"Failed to retrieve calendar events: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return f"An error occurred while retrieving events: {str(e)}"

@function_tool()
async def update_calendar_event_google(
    context: RunContext,
    event_name: str,
    title: Optional[str] = Field(default=None),
    date_time: Optional[str] = Field(default=None),
    duration: Optional[str] = Field(default=None),
    description: Optional[str] = Field(default=None),
    location: Optional[str] = Field(default=None)
) -> str:
    """
    Update an existing Google Calendar event by its name.
    
    TRIGGER WORDS: reschedule, move meeting, change appointment, update event,
    change [event name], reschedule [event name]
    
    Args:
        context: LiveKit agent context
        event_name: Name or partial name of the event to update (e.g., "Meeting with John")
        title: New title (optional)
        date_time: New date/time (optional, e.g., "tomorrow 3pm")
        duration: New duration (optional, e.g., "2 hours")
        description: New description (optional)
        location: New location (optional)
    
    Returns:
        Success message with event details
    """
    try:
        logger.info(f"Updating calendar event: {event_name}")
        
        manager = _get_calendar_manager(context)
        
        # Find event by name
        event = manager.find_event_by_name(event_name)
        
        if not event:
            return f"No event found with name '{event_name}', Sir. Please check the event name and try again."
        
        event_id = event['id']
        current_title = event.get('summary', event_name)
        
        # Update fields
        if title:
            event['summary'] = title
        if description is not None:  # Allow empty string to clear description
            event['description'] = description
        if location is not None:
            event['location'] = location
        if date_time:
            parsed_datetime = parse_datetime_string(date_time, manager.timezone)
            event['start']['dateTime'] = parsed_datetime.isoformat()
            event['start']['timeZone'] = manager.timezone
            
            if duration:
                parsed_duration = parse_duration_string(duration)
                end_time = parsed_datetime + parsed_duration
            else:
                # Calculate duration from existing event if not provided
                if 'end' in event and 'dateTime' in event['end']:
                    end_dt = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                    start_dt = parsed_datetime
                    end_time = end_dt if end_dt > start_dt else start_dt + timedelta(hours=1)
                else:
                    end_time = parsed_datetime + timedelta(hours=1)
            
            event['end']['dateTime'] = end_time.isoformat()
            event['end']['timeZone'] = manager.timezone
        
        manager.update_event(event_id, event)
        
        # Build response message
        updates = []
        if title:
            updates.append(f"title to '{title}'")
        if date_time:
            updates.append(f"time to {parsed_datetime.strftime('%B %d at %I:%M %p')}")
        if location:
            updates.append(f"location to '{location}'")
        
        update_msg = ", ".join(updates) if updates else "details"
        return f"Event '{current_title}' updated successfully, Sir. Changed {update_msg}."
        
    except AuthenticationError:
        return f"Calendar not connected, Sir."
    except APIError as e:
        if "404" in str(e) or "Not Found" in str(e):
            return f"Event '{event_name}' not found, Sir."
        return f"Failed to update event: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return f"An error occurred while updating the event: {str(e)}"

@function_tool()
async def delete_calendar_event_google(
    context: RunContext,
    event_name: str  
) -> str:
    """
    Delete an event from Google Calendar by its name.
    
    TRIGGER WORDS: cancel, delete meeting, remove appointment, delete event,
    cancel [event name], remove [event name]
    
    Args:
        context: LiveKit agent context
        event_name: Name or partial name of the event to delete (e.g., "Meeting with John")
    
    Returns:
        Success message
    """
    try:
        logger.info(f"Deleting calendar event: {event_name}")
        
        manager = _get_calendar_manager(context)
        
        # Find event by name
        event = manager.find_event_by_name(event_name)
        
        if not event:
            return f"No event found with name '{event_name}', Sir. Please check the event name and try again."
        
        event_id = event['id']
        event_title = event.get('summary', event_name)
        
        # Check if there are multiple matches (warn but proceed with first)
        # We could enhance this later to ask user which one
        
        manager.delete_event(event_id)
        return f"Event '{event_title}' deleted successfully, Sir."
        
    except AuthenticationError:
        return f"Calendar not connected, Sir."
    except APIError as e:
        if "404" in str(e) or "Not Found" in str(e):
            return f"Event '{event_name}' not found, Sir."
        return f"Failed to delete event: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return f"An error occurred while deleting the event: {str(e)}"

@function_tool()
async def list_all_events_google(
    context: RunContext,
    max_results: int = 50
) -> str:
    """
    List all upcoming events from Google Calendar.
    
    TRIGGER WORDS: list all events, show all events, everything in calendar
    
    Args:
        context: LiveKit agent context
        max_results: Maximum number of events (default: 50)
    
    Returns:
        Formatted list of events
    """
    try:
        logger.info("Listing all calendar events")
        
        manager = _get_calendar_manager(context)
        user_tz = ZoneInfo(manager.timezone)
        
        now = datetime.now(user_tz)
        now_utc = now.astimezone(ZoneInfo('UTC'))
        
        events = manager.get_events(now_utc, now_utc + timedelta(days=365), max_results)
        
        if not events:
            return "No upcoming events found, Sir."
        
        # Format events
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            title = event.get('summary', 'No Title')
            
            if 'T' in start:
                if start.endswith('Z'):
                    start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                else:
                    start_time = datetime.fromisoformat(start)
                
                if start_time.tzinfo:
                    start_time = start_time.astimezone(user_tz)
                
                formatted = start_time.strftime('%B %d, %Y at %I:%M %p')
                event_list.append(f"{formatted} - {title}")
            else:
                event_list.append(f"{start} - {title}")
        
        return f"Upcoming events, Sir ({len(events)} total):\n" + "\n".join(event_list)
        
    except AuthenticationError:
        return f"Calendar not connected, Sir."
    except APIError as e:
        return f"Failed to list events: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return f"An error occurred: {str(e)}"