import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List
from livekit.agents import function_tool, RunContext

# Google Calendar API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

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
    description: str = "",
    location: str = "",
    attendees: str = ""
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
        description: Event description/details
        location: Event location (physical or virtual)
        attendees: Comma-separated email addresses of attendees
    
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
            'description': description,
            'location': location,
            'start': {
                'dateTime': parsed_datetime.isoformat(),
                'timeZone': 'America/New_York',  # Default timezone
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/New_York',
            },
        }
        
        # Add attendees if provided
        if attendees:
            attendee_list = [email.strip() for email in attendees.split(',') if email.strip()]
            event['attendees'] = [{'email': email} for email in attendee_list]
        
        # Insert event
        event = manager.service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all'  # Send invitations to attendees
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
    date_range: str = "today",
    max_results: int = 10
) -> str:
    """
    MANDATORY CALENDAR VIEWING - View Google Calendar events immediately.
    
    TRIGGER WORDS (use this tool when user says ANY of these):
    - "show my calendar"
    - "what's on my schedule"
    - "view calendar"
    - "check my calendar"
    - "what meetings do I have"
    - "show today's events"
    - "calendar for [date]"
    - "what's on my agenda"
    - "show my schedule"
    - "list my events"
    
    Args:
        date_range: Time range (e.g., "today", "tomorrow", "this week", "next week")
        max_results: Maximum number of events to return
    
    Sir expects immediate calendar viewing when requested.
    """
    try:
        print(f"📅 JARVIS GOOGLE CALENDAR: Viewing events for {date_range}")
        logging.info(f"Viewing Google Calendar events for: {date_range}")
        
        # Get calendar manager
        manager = get_calendar_manager()
        
        # Parse date range
        start_time, end_time = parse_date_range(date_range)
        
        # Get events
        events_result = manager.service.events().list(
            calendarId='primary',
            timeMin=start_time.isoformat() + 'Z',  # Add Z for UTC
            timeMax=end_time.isoformat() + 'Z',    # Add Z for UTC
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"No events found in Google Calendar for {date_range}, Sir."
        
        # Format events
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            # Handle timezone properly
            if 'T' in start:  # Has time component
                try:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                except:
                    # Fallback parsing
                    start_dt = datetime.fromisoformat(start)
            else:  # Date only
                start_dt = datetime.fromisoformat(start)
            
            event_info = f"• {event['summary']} - {start_dt.strftime('%I:%M %p')}"
            
            if 'location' in event and event['location']:
                event_info += f" at {event['location']}"
            
            if 'description' in event and event['description']:
                desc = event['description']
                event_info += f" ({desc[:50]}...)" if len(desc) > 50 else f" ({desc})"
            
            if 'attendees' in event and event['attendees']:
                attendee_emails = [attendee['email'] for attendee in event['attendees']]
                event_info += f" - Attendees: {', '.join(attendee_emails)}"
            
            event_list.append(event_info)
        
        print(f"📅 SUCCESS: Found {len(events)} events in Google Calendar")
        return f"Your Google Calendar for {date_range}, Sir:\n" + "\n".join(event_list)
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error viewing Google Calendar events: {e}")
        return f"Google Calendar viewing failed: {str(e)}"

@function_tool()
async def update_calendar_event_google(
    context: RunContext,  # type: ignore
    event_title: str,
    new_date_time: str = "",
    new_duration: str = "",
    new_description: str = "",
    new_location: str = ""
) -> str:
    """
    MANDATORY CALENDAR UPDATE - Update existing Google Calendar event immediately.
    
    TRIGGER WORDS (use this tool when user says ANY of these):
    - "reschedule [event]"
    - "move meeting"
    - "change appointment"
    - "update event"
    - "postpone meeting"
    - "change time for"
    - "move [event] to"
    - "edit event"
    
    Args:
        event_title: Title of event to update
        new_date_time: New date and time
        new_duration: New duration
        new_description: New description
        new_location: New location
    
    Sir expects immediate calendar updates when requested.
    """
    try:
        print(f"📅 JARVIS GOOGLE CALENDAR: Updating event '{event_title}'")
        logging.info(f"Updating Google Calendar event: {event_title}")
        
        # Get calendar manager
        manager = get_calendar_manager()
        
        # Find the event first
        events_result = manager.service.events().list(
            calendarId='primary',
            q=event_title,
            maxResults=10  # Get more results to find the right event
        ).execute()
        
        events = events_result.get('items', [])
        if not events:
            return f"Event '{event_title}' not found in Google Calendar, Sir."
        
        # Find the most recent event with matching title
        matching_events = [e for e in events if e['summary'].lower() == event_title.lower()]
        if not matching_events:
            return f"Event '{event_title}' not found in Google Calendar, Sir."
        
        event = matching_events[0]  # Use the first matching event
        
        # Check if any updates are provided
        has_updates = any([new_date_time, new_duration, new_description, new_location])
        if not has_updates:
            return f"No updates provided for event '{event_title}', Sir."
        
        # Update fields
        if new_date_time:
            parsed_datetime = parse_datetime_string(new_date_time)
            event['start']['dateTime'] = parsed_datetime.isoformat()
            
            if new_duration:
                parsed_duration = parse_duration_string(new_duration)
                end_time = parsed_datetime + parsed_duration
            else:
                # Keep original duration
                original_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                original_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                duration = original_end - original_start
                end_time = parsed_datetime + duration
            
            event['end']['dateTime'] = end_time.isoformat()
        
        elif new_duration:  # Only duration changed, not time
            # Keep original start time, update end time
            original_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            parsed_duration = parse_duration_string(new_duration)
            end_time = original_start + parsed_duration
            event['end']['dateTime'] = end_time.isoformat()
        
        if new_description:
            event['description'] = new_description
        
        if new_location:
            event['location'] = new_location
        
        # Update event
        updated_event = manager.service.events().update(
            calendarId='primary',
            eventId=event['id'],
            body=event,
            sendUpdates='all'
        ).execute()
        
        print(f"📅 SUCCESS: Event updated in Google Calendar")
        return f"Event '{event_title}' updated successfully in Google Calendar, Sir."
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error updating Google Calendar event: {e}")
        return f"Google Calendar update failed: {str(e)}"

@function_tool()
async def delete_calendar_event_google(
    context: RunContext,  # type: ignore
    event_title: str
) -> str:
    """
    MANDATORY CALENDAR DELETION - Delete Google Calendar event immediately.
    
    TRIGGER WORDS (use this tool when user says ANY of these):
    - "cancel [event]"
    - "delete meeting"
    - "remove appointment"
    - "cancel appointment"
    - "delete event"
    - "remove event"
    
    Args:
        event_title: Title of event to delete
    
    Sir expects immediate calendar deletion when requested.
    """
    try:
        print(f"📅 JARVIS GOOGLE CALENDAR: Deleting event '{event_title}'")
        logging.info(f"Deleting Google Calendar event: {event_title}")
        
        # Get calendar manager
        manager = get_calendar_manager()
        
        # Find the event first
        events_result = manager.service.events().list(
            calendarId='primary',
            q=event_title,
            maxResults=10
        ).execute()
        
        events = events_result.get('items', [])
        if not events:
            return f"Event '{event_title}' not found in Google Calendar, Sir."
        
        # Find the most recent event with matching title
        matching_events = [e for e in events if e['summary'].lower() == event_title.lower()]
        if not matching_events:
            return f"Event '{event_title}' not found in Google Calendar, Sir."
        
        event = matching_events[0]
        
        # Delete event
        manager.service.events().delete(
            calendarId='primary',
            eventId=event['id'],
            sendUpdates='all'
        ).execute()
        
        print(f"📅 SUCCESS: Event deleted from Google Calendar")
        return f"Event '{event_title}' deleted successfully from Google Calendar, Sir."
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error deleting Google Calendar event: {e}")
        return f"Google Calendar deletion failed: {str(e)}"

@function_tool()
async def list_all_events_google(
    context: RunContext  # type: ignore
) -> str:
    """
    MANDATORY CALENDAR LISTING - List all events in Google Calendar.
    
    TRIGGER WORDS (use this tool when user says ANY of these):
    - "list all events"
    - "show all events"
    - "all my events"
    - "everything in my calendar"
    - "list calendar"
    - "show all my meetings"
    
    Sir expects immediate calendar listing when requested.
    """
    try:
        print(f"📅 JARVIS GOOGLE CALENDAR: Listing all events")
        logging.info(f"Listing all Google Calendar events")
        
        # Get calendar manager
        manager = get_calendar_manager()
        
        # Get all events (next 30 days)
        start_time = datetime.now()
        end_time = start_time + timedelta(days=30)
        
        events_result = manager.service.events().list(
            calendarId='primary',
            timeMin=start_time.isoformat() + 'Z',
            timeMax=end_time.isoformat() + 'Z',
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "No events found in your Google Calendar for the next 30 days, Sir."
        
        # Format events
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            # Handle timezone properly
            if 'T' in start:  # Has time component
                try:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                except:
                    start_dt = datetime.fromisoformat(start)
            else:  # Date only
                start_dt = datetime.fromisoformat(start)
            
            event_info = f"• {event['summary']} - {start_dt.strftime('%B %d, %Y at %I:%M %p')}"
            
            if 'location' in event and event['location']:
                event_info += f" at {event['location']}"
            
            event_list.append(event_info)
        
        print(f"📅 SUCCESS: Found {len(events)} events in Google Calendar")
        return f"All events in your Google Calendar (next 30 days), Sir:\n" + "\n".join(event_list)
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error listing all Google Calendar events: {e}")
        return f"Google Calendar listing failed: {str(e)}"

# Helper functions for date/time parsing
def parse_datetime_string(date_time_str: str) -> datetime:
    """Parse various date/time formats"""
    from dateutil import parser
    
    # Handle relative dates
    now = datetime.now()
    
    if "tomorrow" in date_time_str.lower():
        date_time_str = date_time_str.lower().replace("tomorrow", (now + timedelta(days=1)).strftime("%Y-%m-%d"))
    elif "next monday" in date_time_str.lower():
        days_ahead = 7 - now.weekday()  # Monday is 0
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        date_time_str = date_time_str.lower().replace("next monday", (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d"))
    elif "next week" in date_time_str.lower():
        date_time_str = date_time_str.lower().replace("next week", (now + timedelta(weeks=1)).strftime("%Y-%m-%d"))
    elif "next tuesday" in date_time_str.lower():
        days_ahead = (1 - now.weekday()) % 7  # Tuesday is 1
        if days_ahead == 0:
            days_ahead = 7
        date_time_str = date_time_str.lower().replace("next tuesday", (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d"))
    elif "next wednesday" in date_time_str.lower():
        days_ahead = (2 - now.weekday()) % 7  # Wednesday is 2
        if days_ahead == 0:
            days_ahead = 7
        date_time_str = date_time_str.lower().replace("next wednesday", (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d"))
    elif "next thursday" in date_time_str.lower():
        days_ahead = (3 - now.weekday()) % 7  # Thursday is 3
        if days_ahead == 0:
            days_ahead = 7
        date_time_str = date_time_str.lower().replace("next thursday", (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d"))
    elif "next friday" in date_time_str.lower():
        days_ahead = (4 - now.weekday()) % 7  # Friday is 4
        if days_ahead == 0:
            days_ahead = 7
        date_time_str = date_time_str.lower().replace("next friday", (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d"))
    
    try:
        return parser.parse(date_time_str)
    except:
        # Fallback to current time if parsing fails
        return now

def parse_duration_string(duration_str: str) -> timedelta:
    """Parse duration strings like '1 hour', '30 minutes'"""
    duration_str = duration_str.lower()
    
    if "hour" in duration_str:
        hours = int(''.join(filter(str.isdigit, duration_str)))
        return timedelta(hours=hours)
    elif "minute" in duration_str:
        minutes = int(''.join(filter(str.isdigit, duration_str)))
        return timedelta(minutes=minutes)
    else:
        # Default to 1 hour
        return timedelta(hours=1)

def parse_date_range(date_range: str) -> tuple[datetime, datetime]:
    """Parse date range strings"""
    now = datetime.now()
    
    if date_range.lower() == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif date_range.lower() == "tomorrow":
        start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif "this week" in date_range.lower():
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(weeks=1)
    elif "next week" in date_range.lower():
        start = (now + timedelta(weeks=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(weeks=1)
    else:
        # Default to today
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    
    return start, end
