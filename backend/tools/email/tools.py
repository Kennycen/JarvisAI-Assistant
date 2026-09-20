"""Gmail function tools for LiveKit agent"""
from typing import Optional

from livekit.agents import function_tool, RunContext

from tools.email.service import GmailService
from tools.shared.context import get_room_name
from tools.shared.database import get_user_id_from_room
from tools.shared.errors import AuthenticationError, APIError
from tools.shared.logging import setup_tool_logger

logger = setup_tool_logger(__name__)


def _get_user_id_from_context(context: RunContext) -> Optional[str]:
    """Derive user_id from room context via Supabase."""
    room_name = get_room_name(context)
    if not room_name:
        logger.warning("Could not determine room name from context")
        return None

    user_id = get_user_id_from_room(room_name)
    if not user_id:
        logger.warning(f"No user mapped for room: {room_name}")
    return user_id


@function_tool()
async def send_email(
    context: RunContext,
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None,
) -> str:
    """
    JARVIS Email Transmission System. Execute immediately when commanded to send emails.

    TRIGGERS:
    - "send an email"
    - "email this/that to"
    - "forward to"
    - "send this information to"
    - any variation of email sending requests

    Args:
        context: LiveKit agent context (provided by runtime)
        to_email: Target recipient email address
        subject: Message subject line
        message: Email body content
        cc_email: Optional carbon copy recipient

    Returns:
        One-sentence status for the user (JARVIS style)
    """
    try:
        logger.info(f"send_email tool called: to={to_email}, subject='{subject}'")

        # Validate email format early
        if not to_email or "@" not in to_email:
            return "Email sending failed: Invalid recipient email address, Sir."

        user_id = _get_user_id_from_context(context)

        if not user_id:
            return (
                "Email sending failed: Could not determine your account from this room, Sir."
            )

        service = GmailService(user_id)

        result_msg = service.send_email(
            to_email=to_email,
            subject=subject,
            body=message,
            cc_email=cc_email,
        )
        return result_msg

    except AuthenticationError:
        return (
            "Email sending failed: Gmail not connected. "
            "Please connect your Gmail account in settings, Sir."
        )
    except APIError as e:
        return f"Email sending failed: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error in send_email tool: {e}", exc_info=True)
        return f"An error occurred while sending email: {str(e)}"