"""Google Calendar manager - handles all calendar operations"""
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from googleapiclient.discovery import build
from tools.calendar.auth import get_calendar_service
from tools.shared.errors import AuthenticationError, APIError
from tools.shared.logging import setup_tool_logger

logger = setup_tool_logger(__name__)

class GoogleCalendarManager:
    """Manages Google Calendar operations for a user"""
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize calendar manager.
        
        Args:
            user_id: User ID (optional, for fallback auth)
        """
        self.user_id = user_id
        self._service = None
        self._timezone = None
    
    @property
    def service(self):
        """Lazy-load calendar service"""
        if self._service is None:
            try:
                self._service = get_calendar_service(self.user_id)
            except AuthenticationError:
                # Fallback for development
                if self.user_id is None:
                    raise
                logger.warning("Calendar service unavailable")
                raise
        return self._service
    
    @property
    def timezone(self) -> str:
        """Get user's timezone from calendar settings"""
        if self._timezone is None:
            try:
                calendar = self.service.calendarList().get(calendarId='primary').execute()
                self._timezone = calendar.get('timeZone', 'UTC')
                logger.debug(f"Retrieved user timezone: {self._timezone}")
            except Exception as e:
                logger.warning(f"Could not retrieve timezone: {e}")
                self._timezone = 'UTC'
        return self._timezone
    
    def create_event(self, event_data: Dict) -> Dict:
        """
        Create a calendar event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            Created event dictionary
            
        Raises:
            APIError: If event creation fails
        """
        try:
            event = self.service.events().insert(
                calendarId='primary',
                body=event_data,
                sendUpdates='all' if event_data.get('attendees') else 'none'
            ).execute()
            logger.info(f"Event created: {event.get('id')}")
            return event
        except Exception as e:
            raise APIError(f"Failed to create event: {str(e)}")
    
    def get_events(
        self,
        time_min: datetime,
        time_max: datetime,
        max_results: int = 10,
        query: Optional[str] = None
    ) -> List[Dict]:
        """
        Get events from calendar.
        
        Args:
            time_min: Start time (UTC)
            time_max: End time (UTC)
            max_results: Maximum number of results
            query: Optional search query
            
        Returns:
            List of event dictionaries
        """
        try:
            params = {
                'calendarId': 'primary',
                'timeMin': time_min.isoformat().replace('+00:00', 'Z'),
                'timeMax': time_max.isoformat().replace('+00:00', 'Z'),
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            if query:
                params['q'] = query
            
            events_result = self.service.events().list(**params).execute()
            return events_result.get('items', [])
        except Exception as e:
            raise APIError(f"Failed to get events: {str(e)}")
    
    def get_event(self, event_id: str) -> Dict:
        """
        Get a specific event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event dictionary
        """
        try:
            return self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
        except Exception as e:
            raise APIError(f"Failed to get event: {str(e)}")
    
    def find_event_by_name(
        self,
        event_name: str,
        days_back: int = 7,
        days_forward: int = 60
    ) -> Optional[Dict]:
        """
        Find an event by name/title.
        
        Searches for events matching the given name (case-insensitive, partial match).
        If multiple events match, returns the next upcoming one.
        
        Args:
            event_name: Name or partial name of the event
            days_back: How many days back to search (default: 7)
            days_forward: How many days forward to search (default: 60)
            
        Returns:
            Event dictionary if found, None otherwise
        """
        try:
            user_tz = ZoneInfo(self.timezone)
            now = datetime.now(user_tz)
            time_min = now - timedelta(days=days_back)
            time_max = now + timedelta(days=days_forward)
            
            # Search for events using Google Calendar's query parameter
            events = self.get_events(
                time_min.astimezone(ZoneInfo('UTC')),
                time_max.astimezone(ZoneInfo('UTC')),
                max_results=50,
                query=event_name
            )
            
            # Filter events that match (case-insensitive, partial match)
            event_name_lower = event_name.lower()
            matching = [
                e for e in events
                if event_name_lower in e.get('summary', '').lower()
            ]
            
            if not matching:
                logger.debug(f"No events found matching '{event_name}'")
                return None
            
            if len(matching) > 1:
                # If multiple matches, return the next upcoming one
                # Sort by start time (already sorted by API, but ensure it)
                matching.sort(key=lambda e: e.get('start', {}).get('dateTime', ''))
                logger.info(f"Found {len(matching)} events matching '{event_name}', using next upcoming one")
            
            return matching[0]
            
        except Exception as e:
            logger.error(f"Error finding event by name '{event_name}': {e}", exc_info=True)
            raise APIError(f"Failed to find event: {str(e)}")
    
    def update_event(self, event_id: str, event_data: Dict) -> Dict:
        """
        Update an existing event.
        
        Args:
            event_id: Event ID
            event_data: Updated event data
            
        Returns:
            Updated event dictionary
        """
        try:
            return self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event_data
            ).execute()
        except Exception as e:
            raise APIError(f"Failed to update event: {str(e)}")
    
    def delete_event(self, event_id: str) -> None:
        """
        Delete an event.
        
        Args:
            event_id: Event ID to delete
        """
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            logger.info(f"Event deleted: {event_id}")
        except Exception as e:
            raise APIError(f"Failed to delete event: {str(e)}")