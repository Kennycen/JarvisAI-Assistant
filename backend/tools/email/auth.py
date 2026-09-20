"""Gmail authentication utilities"""
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

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_credentials(user_id: str) -> Optional[Credentials]:
    """
    Get Gmail OAuth credentials for a user from Supabase.

    Args:
        user_id: Supabase user id

    Returns:
        Credentials object if found, else None
    """
    if not user_id:
        return None

    try:
        client = get_supabase_client()
        response = (
            client.table("email_credentials")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            logger.warning(f"No Gmail credentials found in Supabase for user: {user_id}")
            return None

        credentials_json = response.data[0]["credentials_json"]
        credentials_dict = json.loads(credentials_json)
        creds = Credentials.from_authorized_user_info(credentials_dict, SCOPES)

        # Refresh if expired and save back
        if creds.expired:
            if creds.refresh_token:
                logger.info(f"Refreshing Gmail credentials for user: {user_id}")
                creds.refresh(Request())
                refreshed_json = creds.to_json()
                client.table("email_credentials").update(
                    {
                        "credentials_json": refreshed_json,
                        "updated_at": "now()",
                    }
                ).eq("user_id", user_id).execute()
            else:
                logger.warning(
                    f"Gmail credentials expired but no refresh token for user: {user_id}"
                )
                return None

        return creds

    except Exception as e:
        logger.error(f"Error fetching Gmail credentials for user {user_id}: {e}", exc_info=True)
        return None


def get_gmail_service(user_id: str):
    """
    Get Gmail API service for a user.

    Args:
        user_id: Supabase user id

    Returns:
        Gmail service instance

    Raises:
        AuthenticationError: if credentials are missing
    """
    creds = get_gmail_credentials(user_id)

    if not creds:
        raise AuthenticationError(
            "Gmail not connected. Please connect your Gmail account in settings."
        )

    return build("gmail", "v1", credentials=creds)