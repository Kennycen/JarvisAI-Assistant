"""Gmail email service wrapper"""
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from googleapiclient.errors import HttpError

from tools.email.auth import get_gmail_service
from tools.shared.errors import APIError, AuthenticationError
from tools.shared.logging import setup_tool_logger

logger = setup_tool_logger(__name__)


class GmailService:
    """High-level Gmail operations for a user"""

    def __init__(self, user_id: str):
        """
        Initialize Gmail service for a user.

        Args:
            user_id: Supabase user id
        """
        self.user_id = user_id
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = get_gmail_service(self.user_id)
        return self._service

    @staticmethod
    def _create_message(
        sender: str,
        to: str,
        subject: str,
        message_text: str,
        cc: Optional[str] = None,
    ):
        """Create a MIME email and encode it for Gmail API."""
        message = MIMEMultipart()
        message["to"] = to
        message["from"] = sender
        message["subject"] = subject

        if cc:
            message["cc"] = cc

        message.attach(MIMEText(message_text, "plain"))

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        return {"raw": raw_message}

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        cc_email: Optional[str] = None,
    ) -> str:
        """
        Send an email using the authenticated user's Gmail account.

        Args:
            to_email: Recipient address
            subject: Subject line
            body: Email body text
            cc_email: Optional CC address

        Returns:
            Human-readable status message
        """
        # Basic validation
        if not to_email or "@" not in to_email:
            raise APIError("Invalid recipient email address.")

        try:
            sender = "me"  # 'me' means the authenticated user in Gmail API
            message_obj = self._create_message(sender, to_email, subject, body, cc_email)

            logger.info(f"Sending email to {to_email}")
            result = (
                self.service.users()
                .messages()
                .send(userId=sender, body=message_obj)
                .execute()
            )

            logger.info(f"Email sent successfully to {to_email}, id={result.get('id')}")
            return f"Email sent successfully to {to_email}, Sir."
        except HttpError as e:
            error_msg = f"Gmail API error: {e}"
            logger.error(error_msg, exc_info=True)
            raise APIError(error_msg)
        except AuthenticationError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error while sending email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise APIError(error_msg)