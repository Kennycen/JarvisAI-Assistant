# tools/google_calendar_tools.py
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from livekit.agents import function_tool, RunContext

# Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Helper functions for parsing dates and durations
def parse_datetime_string(date_str: str) -> datetime:
    """Parse natural language date/time strings"""
    from dateutil import parser
    try:
        return parser.parse(date_str)
    except:
        # Fallback to current time + 1 hour if parsing fails
        return datetime.now() + timedelta(hours=1)

def parse_duration_string(duration_str: str) -> timedelta:
    """Parse duration strings like '1 hour', '30 minutes'"""
    duration_str = duration_str.lower().strip()
    
    if 'hour' in duration_str or 'hr' in duration_str:
        hours = float(''.join(filter(str.isdigit, duration_str.split()[0])))
        return timedelta(hours=hours)
    elif 'minute' in duration_str or 'min' in duration_str:
        minutes = float(''.join(filter(str.isdigit, duration_str.split()[0])))
        return timedelta(minutes=minutes)
    else:
        # Default to 1 hour
        return timedelta(hours=1)

class GoogleCalendarManager:
    """Manages Google Calendar operations"""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            # Check for existing token
            if os.path.exists('token.json'):
                self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # If no valid credentials, authenticate
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # Get credentials from file
                    credentials_file = 'credentials.json'
                    if os.path.exists(credentials_file):
                        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                        self.creds = flow.run_local_server(port=0)
                        
                        # Save credentials
                        with open('token.json', 'w') as token:
                            token.write(self.creds.to_json())
                    else:
                        raise Exception("Google credentials file not found. Please download credentials.json from Google Cloud Console.")
            
            # Build service
            if not self.service:
                self.service = build('calendar', 'v3', credentials=self.creds)
                print("✅ Google Calendar API authenticated successfully!")
                
        except Exception as e:
            logging.error(f"Calendar authentication failed: {e}")
            raise

# Global calendar manager instance
calendar_manager = None

def get_calendar_manager():
    """Get or create calendar manager instance"""
    global calendar_manager
    if calendar_manager is None:
        calendar_manager = GoogleCalendarManager()
    return calendar_manager

@function_tool()
async def add_calendar_event_google(
    context: RunContext,  # type: ignore
    title: str,
    date_time: str,
    duration: str = "1 hour",
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[str] = None
) -> str:
    """
    MANDATORY CALENDAR CONTROL - Add a new event to Google Calendar immediately.
    
    TRIGGER WORDS (use this tool when user says ANY of these):
    - "schedule [event]"
    - "add meeting"
    - "book appointment"
    - "create event"
    - "set up meeting"
    - "add to calendar"
    - "schedule appointment"
    - "book a meeting"
    - "create calendar event"
    
    Args:
        title: Event title/name
        date_time: Date and time (e.g., "tomorrow 2pm", "2024-01-15 14:30", "next Monday 10am")
        duration: Event duration (e.g., "1 hour", "30 minutes", "2 hours")
        description: Event description/details (optional)
        location: Event location (physical or virtual) (optional)
        attendees: Comma-separated email addresses of attendees (optional)
    
    Sir expects immediate calendar execution when scheduling is requested.
    """
    try:
        print(f"📅 JARVIS GOOGLE CALENDAR: Adding event '{title}'")
        logging.info(f"Adding Google Calendar event: {title} at {date_time}")
        
        # Get calendar manager
        manager = get_calendar_manager()
        
        # Parse date and time
        parsed_datetime = parse_datetime_string(date_time)
        parsed_duration = parse_duration_string(duration)
        
        # Calculate end time
        end_time = parsed_datetime + parsed_duration
        
        # Prepare event
        event = {
            'summary': title,
            'start': {
                'dateTime': parsed_datetime.isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/New_York',
            },
        }
        
        # Add optional fields only if provided
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            attendee_list = [email.strip() for email in attendees.split(',') if email.strip()]
            event['attendees'] = [{'email': email} for email in attendee_list]
        
        # Insert event
        event = manager.service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all' if attendees else 'none'
        ).execute()
        
        print(f"📅 SUCCESS: Event created with ID {event['id']}")
        return f"Event '{title}' scheduled successfully in Google Calendar for {parsed_datetime.strftime('%B %d, %Y at %I:%M %p')}, Sir. Duration: {duration}."
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error adding Google Calendar event: {e}")
        return f"Google Calendar operation failed: {str(e)}"

@function_tool()
async def view_calendar_events_google(
    context: RunContext,  # type: ignore
    date: Optional[str] = None,
    max_results: int = 10
) -> str:
    """
    View events from Google Calendar.
    
    TRIGGER WORDS: show calendar, what's on schedule, check calendar, view events, what's today
    
    Args:
        date: Date to view events for (e.g., "today", "tomorrow", "2024-01-15"). Defaults to today.
        max_results: Maximum number of events to return (default: 10)
    """
    try:
        print(f"📅 JARVIS GOOGLE CALENDAR: Viewing events")
        logging.info(f"Viewing Google Calendar events for {date or 'today'}")
        
        manager = get_calendar_manager()
        
        # Parse date
        if date:
            from dateutil import parser
            try:
                target_date = parser.parse(date)
            except:
                target_date = datetime.now()
        else:
            target_date = datetime.now()
        
        # Set time range for the day
        time_min = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        time_max = time_min + timedelta(days=1)
        
        # Get events
        events_result = manager.service.events().list(
            calendarId='primary',
            timeMin=time_min.isoformat() + 'Z',
            timeMax=time_max.isoformat() + 'Z',
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"No events found for {target_date.strftime('%B %d, %Y')}, Sir."
        
        # Format events
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
            title = event.get('summary', 'No Title')
            event_list.append(f"{start_time.strftime('%I:%M %p')} - {title}")
        
        result = f"📅 Events for {target_date.strftime('%B %d, %Y')}, Sir:\n" + "\n".join(event_list)
        print(f"📅 SUCCESS: Found {len(events)} events")
        return result
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error viewing Google Calendar events: {e}")
        return f"Failed to retrieve calendar events: {str(e)}"

@function_tool()
async def update_calendar_event_google(
    context: RunContext,  # type: ignore
    event_id: str,
    title: Optional[str] = None,
    date_time: Optional[str] = None,
    duration: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None
) -> str:
    """
    Update an existing Google Calendar event.
    
    TRIGGER WORDS: reschedule, move meeting, change appointment, update event
    
    Args:
        event_id: The ID of the event to update
        title: New event title (optional)
        date_time: New date and time (optional)
        duration: New duration (optional)
        description: New description (optional)
        location: New location (optional)
    """
    try:
        print(f"📅 JARVIS GOOGLE CALENDAR: Updating event {event_id}")
        logging.info(f"Updating Google Calendar event: {event_id}")
        
        manager = get_calendar_manager()
        
        # Get existing event
        event = manager.service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Update fields
        if title:
            event['summary'] = title
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if date_time:
            parsed_datetime = parse_datetime_string(date_time)
            event['start']['dateTime'] = parsed_datetime.isoformat()
            event['start']['timeZone'] = 'America/New_York'
            
            if duration:
                parsed_duration = parse_duration_string(duration)
                end_time = parsed_datetime + parsed_duration
                event['end']['dateTime'] = end_time.isoformat()
                event['end']['timeZone'] = 'America/New_York'
        
        # Update event
        updated_event = manager.service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()
        
        print(f"📅 SUCCESS: Event updated")
        return f"Event updated successfully, Sir."
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error updating Google Calendar event: {e}")
        return f"Failed to update event: {str(e)}"

@function_tool()
async def delete_calendar_event_google(
    context: RunContext,  # type: ignore
    event_id: str
) -> str:
    """
    Delete an event from Google Calendar.
    
    TRIGGER WORDS: cancel, delete meeting, remove appointment
    
    Args:
        event_id: The ID of the event to delete
    """
    try:
        print(f"📅 JARVIS GOOGLE CALENDAR: Deleting event {event_id}")
        logging.info(f"Deleting Google Calendar event: {event_id}")
        
        manager = get_calendar_manager()
        
        # Delete event
        manager.service.events().delete(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        print(f"📅 SUCCESS: Event deleted")
        return f"Event deleted successfully, Sir."
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error deleting Google Calendar event: {e}")
        return f"Failed to delete event: {str(e)}"

@function_tool()
async def list_all_events_google(
    context: RunContext,  # type: ignore
    max_results: int = 50
) -> str:
    """
    List all upcoming events from Google Calendar.
    
    TRIGGER WORDS: list all events, show all events, everything in calendar
    
    Args:
        max_results: Maximum number of events to return (default: 50)
    """
    try:
        print(f"📅 JARVIS GOOGLE CALENDAR: Listing all events")
        logging.info(f"Listing all Google Calendar events")
        
        manager = get_calendar_manager()
        
        # Get events from now onwards
        now = datetime.utcnow().isoformat() + 'Z'
        
        events_result = manager.service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "No upcoming events found, Sir."
        
        # Format events
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
            title = event.get('summary', 'No Title')
            event_list.append(f"{start_time.strftime('%B %d, %Y at %I:%M %p')} - {title}")
        
        result = f"📅 Upcoming events, Sir ({len(events)} total):\n" + "\n".join(event_list)
        print(f"📅 SUCCESS: Found {len(events)} events")
        return result
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error listing Google Calendar events: {e}")
        return f"Failed to list events: {str(e)}"