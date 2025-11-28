# tools/email_tools.py
import logging
import os
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from livekit.agents import function_tool, RunContext
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from supabase import create_client
from tools.room_context import get_current_room_name

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Supabase client cache
_supabase_client_cache = None

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
    if not room_name:
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

def get_gmail_service(room_name: str = None):
    """Get Gmail service instance for user"""
    user_id = None
    
    # Try to get user_id from room if provided
    if room_name:
        user_id = get_user_id_from_room(room_name)
    
    if not user_id:
        print("⚠️ WARNING: Could not get user_id. Will try fallback credentials.")
        # Fallback to env vars for development
        return None
    
    try:
        print(f"🔍 DEBUG: Fetching Gmail credentials for user: {user_id}")
        client = get_supabase_client()
        response = client.table("email_credentials").select("*").eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"🔍 DEBUG: Found Gmail credentials in Supabase")
            credentials_json = response.data[0]["credentials_json"]
            credentials_dict = json.loads(credentials_json)
            creds = Credentials.from_authorized_user_info(credentials_dict, SCOPES)
            
            # Refresh if expired and save back to database
            if creds.expired:
                print(f"🔍 DEBUG: Credentials expired, refreshing...")
                if creds.refresh_token:
                    creds.refresh(Request())
                    print(f"🔍 DEBUG: Credentials refreshed successfully")
                    
                    # Save refreshed credentials back to database
                    refreshed_json = creds.to_json()
                    client.table("email_credentials").update({
                        "credentials_json": refreshed_json,
                        "updated_at": "now()"
                    }).eq("user_id", user_id).execute()
                    print(f"🔍 DEBUG: Refreshed credentials saved to database")
                else:
                    print(f"⚠️ WARNING: Credentials expired but no refresh token")
                    return None
            
            service = build('gmail', 'v1', credentials=creds)
            print(f"✅ Gmail API authenticated for user {user_id}")
            return service
        else:
            print(f"⚠️ WARNING: No Gmail credentials found in Supabase for user: {user_id}")
            return None
            
    except Exception as e:
        logging.error(f"Gmail authentication failed: {e}")
        print(f"🔍 DEBUG: Gmail authentication error: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_message(sender: str, to: str, subject: str, message_text: str, cc: Optional[str] = None):
    """Create a message for an email."""
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    if cc:
        message['cc'] = cc
    
    message.attach(MIMEText(message_text, 'plain'))
    
    # Encode message in base64url format
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

def send_message(service, user_id: str, message):
    """Send an email message."""
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"📧 Message sent! Message Id: {message['id']}")
        return message
    except HttpError as error:
        print(f"📧 ERROR: An error occurred: {error}")
        raise

@function_tool()    
async def send_email(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """
    JARVIS Email Transmission System. Execute immediately when commanded to send emails.
    
    MANDATORY USAGE: Use this tool every time the user mentions:
    - "send an email" 
    - "email this/that to"
    - "forward to"
    - "send this information to"
    - Any variation of email sending requests
    
    Args:
        to_email: Target recipient email address
        subject: Message subject line  
        message: Email body content
        cc_email: Optional carbon copy recipient
    
    Sir expects immediate execution when email transmission is requested.
    """
    try:
        logging.info(f"send_email function called: to={to_email}, subject='{subject}'")
        print(f"📧 EMAIL TOOL CALLED: Sending to {to_email}")
        
        # Get room name from context
        room_name = get_room_name_from_context(context)
        
        if not room_name:
            print("⚠️ WARNING: Could not extract room name. Will try to use fallback credentials.")
        
        # Validate email format
        if not to_email or '@' not in to_email:
            return "Email sending failed: Invalid recipient email address."
        
        # Get Gmail service
        service = get_gmail_service(room_name)
        
        if not service:
            return "Email sending failed: Gmail not connected. Please connect your Gmail account in settings."
        
        # Get sender email from user's profile (from credentials)
        # For now, we'll use 'me' which refers to the authenticated user
        sender = 'me'
        
        # Create and send message
        message_obj = create_message(sender, to_email, subject, message, cc_email)
        result = send_message(service, sender, message_obj)
        
        logging.info(f"Email sent successfully to {to_email}")
        return f"Email sent successfully to {to_email}, Sir."
        
    except HttpError as error:
        error_msg = f"Gmail API error: {error}"
        logging.error(error_msg)
        print(f"📧 ERROR: {error_msg}")
        return f"Email sending failed: {error_msg}"
    except Exception as e:
        error_msg = f"An error occurred while sending email: {str(e)}"
        logging.error(error_msg)
        print(f"📧 ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg