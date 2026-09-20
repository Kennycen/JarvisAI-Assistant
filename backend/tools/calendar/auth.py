"""Google Calendar authentication utilities"""
import os
import json
import logging
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from tools.shared.database import get_supabase_client
from tools.shared.errors import AuthenticationError
from tools.shared.logging import setup_tool_logger

logger = setup_tool_logger(__name__)

# Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_credentials(user_id: str) -> Optional[Credentials]:
    """
    Get Google Calendar credentials for a user from Supabase.
    
    Args:
        user_id: User ID to fetch credentials for
        
    Returns:
        Credentials object if found, None otherwise
    """
    if not user_id:
        return None
        
    try:
        client = get_supabase_client()
        response = client.table("calendar_credentials").select("*").eq(
            "user_id", user_id
        ).execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"No calendar credentials found for user: {user_id}")
            return None
        
        credentials_json = response.data[0]["credentials_json"]
        credentials_dict = json.loads(credentials_json)
        creds = Credentials.from_authorized_user_info(credentials_dict, SCOPES)
        
        # Refresh if expired
        if creds.expired:
            if creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed credentials back
                refreshed_json = creds.to_json()
                client.table("calendar_credentials").update({
                    "credentials_json": refreshed_json,
                    "updated_at": "now()"
                }).eq("user_id", user_id).execute()
                logger.info(f"Refreshed calendar credentials for user: {user_id}")
            else:
                logger.warning(f"Credentials expired but no refresh token for user: {user_id}")
                return None
        
        return creds
        
    except Exception as e:
        logger.error(f"Error fetching calendar credentials: {e}", exc_info=True)
        return None

def get_calendar_service(user_id: str):
    """
    Get Google Calendar service instance for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        Google Calendar service instance
        
    Raises:
        AuthenticationError: If credentials are not available
    """
    creds = get_calendar_credentials(user_id)
    
    if not creds:
        # Fallback to token.json for development
        if os.path.exists('token.json'):
            logger.debug("Using fallback token.json for development")
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
        else:
            raise AuthenticationError(
                "Calendar not connected. Please connect your Google Calendar account."
            )
    
    return build('calendar', 'v3', credentials=creds)