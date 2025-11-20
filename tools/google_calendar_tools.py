import os
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Union
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from livekit.agents import function_tool, RunContext
from supabase import create_client
from dotenv import load_dotenv
from tools.room_context import get_current_room_name
from zoneinfo import ZoneInfo

load_dotenv()

# Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Add at module level (after imports)
_supabase_client_cache = None

def get_room_name_from_context(context):
    """Helper function to get room name from multiple sources"""
    room_name = None
    
    # Method 1: Get from global storage (most reliable)
    try:
        room_name = get_current_room_name()
        if room_name:
            print(f"🔍 DEBUG: Got room name from global storage: {room_name}")
            return room_name
    except:
        pass
    
    # Method 2: Try to get from context
    try:
        if hasattr(context, 'room') and hasattr(context.room, 'name'):
            room_name = context.room.name
            print(f"🔍 DEBUG: Got room name from context.room.name: {room_name}")
            return room_name
        elif hasattr(context, 'room_name'):
            room_name = context.room_name
            print(f"🔍 DEBUG: Got room name from context.room_name: {room_name}")
            return room_name
    except Exception as e:
        print(f"🔍 DEBUG: Error getting room name from context: {e}")
    
    return None

def get_supabase_client():
    """Get Supabase client for agent worker (singleton pattern)"""
    global _supabase_client_cache
    
    if _supabase_client_cache is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise Exception("Supabase credentials not found in environment")
        
        _supabase_client_cache = create_client(supabase_url, supabase_key)
    
    return _supabase_client_cache

def get_user_id_from_room(room_name: str) -> str:
    """Get user_id from room name"""
    try:
        print(f"🔍 DEBUG: Looking up user_id for room: {room_name}")
        client = get_supabase_client()
        response = client.table("rooms").select("user_id").eq("room_name", room_name).execute()
        
        if response.data and len(response.data) > 0:
            user_id = response.data[0]["user_id"]
            print(f"🔍 DEBUG: Found user_id: {user_id} for room: {room_name}")
            return user_id
        else:
            print(f"⚠️ WARNING: No user found for room: {room_name}")
            return None
    except Exception as e:
        logging.error(f"Error getting user from room: {e}")
        print(f"🔍 DEBUG: Error in get_user_id_from_room: {e}")
        import traceback
        traceback.print_exc()
        return None

# Helper functions for parsing dates and durations
def parse_datetime_string(date_str: str, user_timezone: str = 'UTC') -> datetime:
    """Parse natural language date/time strings with proper timezone handling"""
    from dateutil import parser
    
    # Get timezone object
    try:
        tz = ZoneInfo(user_timezone)
    except:
        # Fallback to UTC if timezone is invalid
        tz = ZoneInfo('UTC')
    
    # Get current time in user's timezone as reference
    now = datetime.now(tz)
    
    # Normalize the date string for better parsing
    date_str_lower = date_str.lower().strip()
    
    try:
        # Handle relative dates explicitly
        if 'tomorrow' in date_str_lower:
            # Extract time if present
            if any(time_word in date_str_lower for time_word in ['am', 'pm', ':', 'at']):
                # Parse the time part (remove "tomorrow" and parse time)
                time_part = date_str_lower.replace('tomorrow', '').strip()
                # Use tomorrow as the default date
                tomorrow = now + timedelta(days=1)
                parsed = parser.parse(time_part, default=tomorrow)
            else:
                # Default to 9am tomorrow if no time specified
                tomorrow = now + timedelta(days=1)
                parsed = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        elif 'today' in date_str_lower:
            # Extract time if present
            if any(time_word in date_str_lower for time_word in ['am', 'pm', ':', 'at']):
                time_part = date_str_lower.replace('today', '').strip()
                parsed = parser.parse(time_part, default=now)
            else:
                # Default to 1 hour from now if no time specified
                parsed = now + timedelta(hours=1)
        elif 'next week' in date_str_lower:
            parsed = parser.parse(date_str_lower, default=now + timedelta(days=7))
        elif 'next' in date_str_lower:
            # Handle "next [day of week]" patterns like "next Tuesday", "next Monday"
            days_of_week = {
                'monday': 0, 'mon': 0,
                'tuesday': 1, 'tue': 1, 'tues': 1,
                'wednesday': 2, 'wed': 2,
                'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
                'friday': 4, 'fri': 4,
                'saturday': 5, 'sat': 5,
                'sunday': 6, 'sun': 6
            }
            
            # Find the day of week in the string
            target_day = None
            for day_name, day_num in days_of_week.items():
                if day_name in date_str_lower:
                    target_day = day_num
                    break
            
            if target_day is not None:
                # Calculate days until next occurrence of that day
                # Use date only (midnight) for calculation to avoid timezone issues
                now_date_only = now.replace(hour=0, minute=0, second=0, microsecond=0)
                current_day = now_date_only.weekday()  # Monday = 0, Sunday = 6
                days_ahead = target_day - current_day
                
                # If the day has already passed this week OR it's today, get next week's occurrence
                if days_ahead <= 0:
                    days_ahead += 7
                
                # Calculate the target date (date only, no time)
                target_date = now_date_only + timedelta(days=days_ahead)
                
                # Extract time if present
                if any(time_word in date_str_lower for time_word in ['am', 'pm', ':', 'at']):
                    # Try to parse time from the string
                    time_part = date_str_lower.replace('next', '').strip()
                    # Remove day name from time part
                    for day_name in days_of_week.keys():
                        time_part = time_part.replace(day_name, '').strip()
                    
                    if time_part:
                        try:
                            # Parse just the time part
                            from dateutil import parser
                            time_parsed = parser.parse(time_part, default=target_date)
                            parsed = time_parsed
                        except:
                            # If time parsing fails, default to 9am
                            parsed = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                    else:
                        parsed = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                else:
                    # Default to 9am if no time specified (but this will be reset to midnight in view function)
                    parsed = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                # "next" without a day of week - use generic parser
                parsed = parser.parse(date_str, default=now + timedelta(days=7))
        else:
            # Use dateutil parser with current time as default
            parsed = parser.parse(date_str, default=now)
        
        # If parsed datetime is naive, make it timezone-aware
        if parsed.tzinfo is None:
            # Assume it's in the user's timezone
            parsed = parsed.replace(tzinfo=tz)
        else:
            # Convert to user's timezone if it has a different timezone
            parsed = parsed.astimezone(tz)
        
        return parsed
        
    except Exception as e:
        logging.warning(f"Failed to parse date string '{date_str}': {e}")
        # Fallback to 1 hour from now in user's timezone
        return now + timedelta(hours=1)

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
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.creds = None
        self.service = None
        self.timezone = None  # Cache the user's timezone
        self._authenticate()
        self._get_timezone()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            print(f"🔍 DEBUG: Authenticating calendar manager for user_id: {self.user_id}")
            
            # If user_id provided, get credentials from Supabase
            if self.user_id:
                print(f"🔍 DEBUG: Fetching credentials from Supabase for user: {self.user_id}")
                client = get_supabase_client()
                response = client.table("calendar_credentials").select("*").eq(
                    "user_id", self.user_id
                ).execute()
                
                if response.data and len(response.data) > 0:
                    print(f"🔍 DEBUG: Found credentials in Supabase")
                    credentials_json = response.data[0]["credentials_json"]
                    credentials_dict = json.loads(credentials_json)
                    self.creds = Credentials.from_authorized_user_info(
                        credentials_dict, SCOPES
                    )
                    
                    # Refresh if expired
                    if self.creds.expired:
                        print(f"🔍 DEBUG: Credentials expired, refreshing...")
                        if self.creds.refresh_token:
                            self.creds.refresh(Request())
                            print(f"🔍 DEBUG: Credentials refreshed successfully")
                        else:
                            print(f"⚠️ WARNING: Credentials expired but no refresh token")
                    
                    self.service = build('calendar', 'v3', credentials=self.creds)
                    print(f"✅ Google Calendar API authenticated for user {self.user_id}")
                    return
                else:
                    print(f"⚠️ WARNING: No credentials found in Supabase for user: {self.user_id}")
            
            # Fallback to token.json for development
            if os.path.exists('token.json'):
                print(f"🔍 DEBUG: Using fallback token.json")
                self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            else:
                print(f"⚠️ WARNING: token.json not found")
            
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    print(f"🔍 DEBUG: Refreshing expired credentials from token.json")
                    self.creds.refresh(Request())
                else:
                    raise Exception("No valid calendar credentials found")
            
            if not self.service:
                self.service = build('calendar', 'v3', credentials=self.creds)
                print("✅ Google Calendar API authenticated successfully!")
                
        except Exception as e:
            logging.error(f"Calendar authentication failed: {e}")
            print(f"🔍 DEBUG: Authentication error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _get_timezone(self):
        """Get user's timezone from Google Calendar settings"""
        try:
            if not self.service:
                # Fallback to UTC if service not available
                self.timezone = 'UTC'
                print(f"⚠️ WARNING: Service not available, using UTC as fallback timezone")
                return
            
            # Get calendar metadata which includes timezone
            calendar = self.service.calendarList().get(calendarId='primary').execute()
            self.timezone = calendar.get('timeZone', 'UTC')
            print(f"🔍 DEBUG: Retrieved user timezone: {self.timezone}")
        except Exception as e:
            logging.warning(f"Could not retrieve timezone from Google Calendar: {e}")
            # Fallback to UTC
            self.timezone = 'UTC'
            print(f"⚠️ WARNING: Using UTC as fallback timezone: {e}")

# Global calendar manager instance
calendar_manager = None

def get_calendar_manager(room_name: str = None):
    """Get or create calendar manager instance"""
    user_id = None
    
    # Try to get user_id from room if provided
    if room_name:
        user_id = get_user_id_from_room(room_name)
    
    # Create manager with user_id (or None for fallback)
    return GoogleCalendarManager(user_id=user_id)

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
        title: Event title/name (required)
        date_time: Date and time (required, e.g., "tomorrow 2pm", "2024-01-15 14:30", "next Monday 10am")
        duration: Event duration (default: "1 hour", e.g., "30 minutes", "2 hours")
        description: Event description/details (optional, default: empty string)
        location: Event location (optional, default: empty string)
        attendees: Comma-separated email addresses of attendees (optional, default: empty string)
    
    Sir expects immediate calendar execution when scheduling is requested.
    """
    try:
        # Parameters already have defaults, no conversion needed
        
        # Try multiple ways to get room name
        room_name = None
        
        # Method 1: Get from global storage (most reliable)
        try:
            room_name = get_current_room_name()
            if room_name:
                print(f"🔍 DEBUG: Got room name from global storage: {room_name}")
        except:
            pass
        
        # Method 2: Try to get from context
        if not room_name:
            try:
                if hasattr(context, 'room') and hasattr(context.room, 'name'):
                    room_name = context.room.name
                    print(f"🔍 DEBUG: Got room name from context.room.name: {room_name}")
                elif hasattr(context, 'room_name'):
                    room_name = context.room_name
                    print(f"🔍 DEBUG: Got room name from context.room_name: {room_name}")
            except Exception as e:
                print(f"🔍 DEBUG: Error getting room name from context: {e}")
        
        if not room_name:
            print("⚠️ WARNING: Could not extract room name. Will try to use fallback credentials.")
        
        print(f"📅 JARVIS GOOGLE CALENDAR: Adding event '{title}'")
        print(f"🔍 DEBUG: Room name: {room_name}")
        logging.info(f"Adding Google Calendar event: {title} at {date_time}, room: {room_name}")
        
        # Get calendar manager with room context
        manager = get_calendar_manager(room_name)
        
        # Verify manager has service
        if not manager.service:
            raise Exception("Calendar service not initialized. Check credentials.")
        
        print(f"🔍 DEBUG: Calendar manager initialized. User ID: {manager.user_id}")
        
        # Parse date and time using user's timezone
        parsed_datetime = parse_datetime_string(date_time, manager.timezone)
        parsed_duration = parse_duration_string(duration)
        
        print(f"🔍 DEBUG: Parsed datetime: {parsed_datetime}, duration: {parsed_duration}")
        
        # Calculate end time
        end_time = parsed_datetime + parsed_duration
        
        # Prepare event - use the user's timezone from calendar
        event = {
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
        
        # Add optional fields only if provided (not empty)
        if description and description.strip():
            event['description'] = description
        if location and location.strip():
            event['location'] = location
        
        # Handle attendees - only add if we have valid emails
        if attendees and attendees.strip():
            attendee_list = [email.strip() for email in attendees.split(',') if email.strip()]
            # Only add attendees if we have at least one valid email
            if attendee_list:
                # Basic email validation - check for @ symbol
                valid_emails = [email for email in attendee_list if '@' in email and '.' in email.split('@')[1] if '@' in email]
                if valid_emails:
                    event['attendees'] = [{'email': email} for email in valid_emails]
                    print(f"🔍 DEBUG: Added {len(valid_emails)} attendees: {valid_emails}")
                else:
                    print(f"⚠️ WARNING: No valid email addresses found in attendees: {attendees}")
            else:
                print(f"🔍 DEBUG: No attendees to add (empty list after parsing)")
                
        # Insert event
        print("🔍 DEBUG: Attempting to insert event into Google Calendar...")
        event_result = manager.service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all' if event.get('attendees') else 'none'  # Only send updates if we actually have attendees
        ).execute()
        
        print(f"📅 SUCCESS: Event created with ID {event_result['id']}")
        
        return f"Event '{title}' scheduled successfully in Google Calendar for {parsed_datetime.strftime('%B %d, %Y at %I:%M %p')}, Sir. Duration: {duration}."
        
    except Exception as e:
        error_msg = str(e)
        print(f"📅 ERROR: {error_msg}")
        print(f"🔍 DEBUG: Full error traceback:")
        import traceback
        traceback.print_exc()
        logging.error(f"Error adding Google Calendar event: {e}", exc_info=True)
        return f"Google Calendar operation failed: {error_msg}"


    """
    View events from Google Calendar.
    
    TRIGGER WORDS: show calendar, what's on schedule, check calendar, view events, what's today
    
    Args:
        date: Date to view events for (e.g., "today", "tomorrow", "2024-01-15"). Defaults to today.
        max_results: Maximum number of events to return (default: 10)
    """
    try:
        # Get room name using helper function
        room_name = get_room_name_from_context(context)
        
        if not room_name:
            print("⚠️ WARNING: Could not extract room name. Will try to use fallback credentials.")
        
        print(f"📅 JARVIS GOOGLE CALENDAR: Viewing events")
        logging.info(f"Viewing Google Calendar events for {date or 'today'}")
        
        manager = get_calendar_manager(room_name)
        
        # Get timezone for date parsing
        user_tz = ZoneInfo(manager.timezone) if manager.timezone else ZoneInfo('UTC')
        
        # Parse date
        if date:
            target_date = parse_datetime_string(date, manager.timezone)
            # For date queries, we only care about the date, not the time
            # Reset to start of day in user's timezone
            target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            target_date = datetime.now(user_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Determine if this is a date range query
        is_range_query = False
        date_lower = date.lower().strip() if date else ""
        
        # Check for range queries FIRST, before single day logic
        if 'next week' in date_lower:
            is_range_query = True
            # Calculate next Monday
            current_day = target_date.weekday()  # Use target_date, not now
            days_ahead = 7 - current_day  # Monday is 0
            if days_ahead == 0:  # If target date is Monday, go to next Monday
                days_ahead = 7
            time_min = target_date + timedelta(days=days_ahead)
            time_max = time_min + timedelta(days=7)  # 7 days for a week
            range_description = f"next week (starting {time_min.strftime('%B %d')})"
        elif 'this week' in date_lower:
            is_range_query = True
            # Start from Monday of current week
            days_back = target_date.weekday()
            time_min = target_date - timedelta(days=days_back)
            time_max = time_min + timedelta(days=7)  # 7 days for a week
            range_description = f"this week (starting {time_min.strftime('%B %d')})"
        else:
            # Single day query - use the date we parsed (already reset to midnight)
            time_min = target_date
            time_max = time_min + timedelta(days=1)
            range_description = target_date.strftime('%B %d, %Y')
        
        # Add debug logging
        print(f"🔍 DEBUG: Query date: {date}, Parsed: {target_date}, Range: {time_min} to {time_max}")
        
        # Set time range for the day (in user's timezone)
        time_min_utc = time_min.astimezone(ZoneInfo('UTC'))
        time_max_utc = time_max.astimezone(ZoneInfo('UTC'))
        
        # Get events
        events_result = manager.service.events().list(
            calendarId='primary',
            timeMin=time_min_utc.isoformat().replace('+00:00', 'Z'),
            timeMax=time_max_utc.isoformat().replace('+00:00', 'Z'),
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            if is_range_query:
                return f"No events found for {range_description}, Sir."
            else:
                return f"No events found for {range_description}, Sir."
        
        # Format events
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if 'T' in start:
                # Parse as datetime with timezone
                if start.endswith('Z'):
                    start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                else:
                    start_time = datetime.fromisoformat(start)
                # Convert to user's timezone for display
                if start_time.tzinfo:
                    start_time = start_time.astimezone(user_tz)
                title = event.get('summary', 'No Title')
                event_list.append(f"{start_time.strftime('%I:%M %p')} - {title}")
            else:
                # All-day event
                title = event.get('summary', 'No Title')
                event_list.append(f"All day - {title}")
        
        result = f"📅 Events for {target_date.strftime('%B %d, %Y')}, Sir:\n" + "\n".join(event_list)
        print(f"📅 SUCCESS: Found {len(events)} events")
        return result
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error viewing Google Calendar events: {e}")
        return f"Failed to retrieve calendar events: {str(e)}"

@function_tool()
async def view_calendar_events_google(
    context: RunContext,  # type: ignore
    date: Optional[str] = None,
    max_results: int = 10
) -> str:
    """
    View events from Google Calendar for a specific date or date range.
    
    TRIGGER WORDS: show calendar, what's on schedule, check calendar, view events, what's today, next week, this week, upcoming events, events for
    
    Args:
        date: Date or date range to view events for (e.g., "today", "tomorrow", "2024-01-15", "next week", "this week"). Defaults to today.
        max_results: Maximum number of events to return (default: 10)
    """
    try:
        # Get room name using helper function
        room_name = get_room_name_from_context(context)
        
        if not room_name:
            print("⚠️ WARNING: Could not extract room name. Will try to use fallback credentials.")
        
        print(f"📅 JARVIS GOOGLE CALENDAR: Viewing events")
        logging.info(f"Viewing Google Calendar events for {date or 'today'}")
        
        manager = get_calendar_manager(room_name)
        
        # Get timezone for date parsing
        user_tz = ZoneInfo(manager.timezone) if manager.timezone else ZoneInfo('UTC')
        
        # Determine if this is a date range query
        is_range_query = False
        date_lower = date.lower().strip() if date else ""
        
        if date:
            target_date = parse_datetime_string(date, manager.timezone)
            # For date queries, we only care about the date, not the time
            # Reset to start of day in user's timezone
            target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            target_date = datetime.now(user_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Determine if this is a date range query
        is_range_query = False
        date_lower = date.lower().strip() if date else ""
        
        # Check for range queries FIRST, before single day logic
        if 'next week' in date_lower:
            is_range_query = True
            # Calculate next Monday
            current_day = target_date.weekday()  # Use target_date, not now
            days_ahead = 7 - current_day  # Monday is 0
            if days_ahead == 0:  # If target date is Monday, go to next Monday
                days_ahead = 7
            time_min = target_date + timedelta(days=days_ahead)
            time_max = time_min + timedelta(days=7)  # 7 days for a week
            range_description = f"next week (starting {time_min.strftime('%B %d')})"
        elif 'this week' in date_lower:
            is_range_query = True
            # Start from Monday of current week
            days_back = target_date.weekday()
            time_min = target_date - timedelta(days=days_back)
            time_max = time_min + timedelta(days=7)  # 7 days for a week
            range_description = f"this week (starting {time_min.strftime('%B %d')})"
        else:
            # Single day query - use the date we parsed (already reset to midnight)
            time_min = target_date
            time_max = time_min + timedelta(days=1)
            range_description = target_date.strftime('%B %d, %Y')
        
        # Add debug logging
        print(f"🔍 DEBUG: Query date: {date}, Parsed: {target_date}, Range: {time_min} to {time_max}")
        
        # Convert to UTC for API call
        time_min_utc = time_min.astimezone(ZoneInfo('UTC'))
        time_max_utc = time_max.astimezone(ZoneInfo('UTC'))
        
        # Get events
        events_result = manager.service.events().list(
            calendarId='primary',
            timeMin=time_min_utc.isoformat().replace('+00:00', 'Z'),
            timeMax=time_max_utc.isoformat().replace('+00:00', 'Z'),
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            if is_range_query:
                return f"No events found for {range_description}, Sir."
            else:
                return f"No events found for {range_description}, Sir."
        
        # Format events
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if 'T' in start:
                # Parse as datetime with timezone
                if start.endswith('Z'):
                    start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                else:
                    start_time = datetime.fromisoformat(start)
                # Convert to user's timezone for display
                if start_time.tzinfo:
                    start_time = start_time.astimezone(user_tz)
                title = event.get('summary', 'No Title')
                # Include date for range queries
                if is_range_query:
                    event_list.append(f"{start_time.strftime('%B %d at %I:%M %p')} - {title}")
                else:
                    event_list.append(f"{start_time.strftime('%I:%M %p')} - {title}")
            else:
                # All-day event
                title = event.get('summary', 'No Title')
                event_list.append(f"All day - {title}")
        
        result = f"📅 Events for {range_description}, Sir ({len(events)} total):\n" + "\n".join(event_list)
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
        # Try to get room name from context
        room_name = None
        try:
            if hasattr(context, 'room') and hasattr(context.room, 'name'):
                room_name = context.room.name
        except:
            pass
        
        print(f"📅 JARVIS GOOGLE CALENDAR: Updating event {event_id}")
        logging.info(f"Updating Google Calendar event: {event_id}")
        
        manager = get_calendar_manager(room_name)
        
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
            parsed_datetime = parse_datetime_string(date_time, manager.timezone)
            event['start']['dateTime'] = parsed_datetime.isoformat()
            event['start']['timeZone'] = manager.timezone
            
            if duration:
                parsed_duration = parse_duration_string(duration)
                end_time = parsed_datetime + parsed_duration
                event['end']['dateTime'] = end_time.isoformat()
                event['end']['timeZone'] = manager.timezone
        
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
        # Try to get room name from context
        room_name = None
        try:
            if hasattr(context, 'room') and hasattr(context.room, 'name'):
                room_name = context.room.name
        except:
            pass
        
        print(f"📅 JARVIS GOOGLE CALENDAR: Deleting event {event_id}")
        logging.info(f"Deleting Google Calendar event: {event_id}")
        
        manager = get_calendar_manager(room_name)
        
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
        # Try to get room name from context
        room_name = None
        try:
            if hasattr(context, 'room') and hasattr(context.room, 'name'):
                room_name = context.room.name
        except:
            pass
        
        print(f"📅 JARVIS GOOGLE CALENDAR: Listing all events")
        logging.info(f"Listing all Google Calendar events")
        
        manager = get_calendar_manager(room_name)
        
        # Get timezone for date parsing
        user_tz = ZoneInfo(manager.timezone) if manager.timezone else ZoneInfo('UTC')
        
        # Get events from now onwards (in user's timezone, then convert to UTC)
        now = datetime.now(user_tz)
        now_utc = now.astimezone(ZoneInfo('UTC'))
        
        events_result = manager.service.events().list(
            calendarId='primary',
            timeMin=now_utc.isoformat().replace('+00:00', 'Z'),
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
            if 'T' in start:
                # Parse as datetime with timezone
                if start.endswith('Z'):
                    start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                else:
                    start_time = datetime.fromisoformat(start)
                # Convert to user's timezone for display
                if start_time.tzinfo:
                    start_time = start_time.astimezone(user_tz)
                title = event.get('summary', 'No Title')
                event_list.append(f"{start_time.strftime('%B %d, %Y at %I:%M %p')} - {title}")
            else:
                # All-day event
                title = event.get('summary', 'No Title')
                event_list.append(f"{start} - {title}")
        
        result = f"📅 Upcoming events, Sir ({len(events)} total):\n" + "\n".join(event_list)
        print(f"📅 SUCCESS: Found {len(events)} events")
        return result
        
    except Exception as e:
        print(f"📅 ERROR: {e}")
        logging.error(f"Error listing Google Calendar events: {e}")
        return f"Failed to list events: {str(e)}"