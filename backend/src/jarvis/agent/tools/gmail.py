from __future__ import annotations

import asyncio

from livekit.agents import RunContext, function_tool

from jarvis.agent.deps import gmail
from jarvis.core.errors import JarvisError

# Google's client library is synchronous. Every call goes through asyncio.to_thread
# so it never blocks the event loop - blocking it causes audible audio stutter.


@function_tool()
async def search_email(context: RunContext, query: str, limit: int = 5) -> str:
    """Search the user's Gmail and return a short summary of matching messages.

    Args:
        query: A Gmail search query, e.g. "is:unread", "from:mom", "subject:invoice".
        limit: Maximum number of messages to return.
    """
    try:
        messages = await asyncio.to_thread(gmail().search, query, limit)
    except JarvisError as exc:
        return str(exc)

    if not messages:
        return f"No messages matched {query}."

    lines = [
        f"[{m.id}] from {m.sender}, subject: {m.subject}. {m.snippet[:120]}" for m in messages
    ]
    return "\n".join(lines)


@function_tool()
async def read_email(context: RunContext, message_id: str) -> str:
    """Read the full body of one email. Get the message_id from search_email first."""
    try:
        message = await asyncio.to_thread(gmail().read, message_id)
    except JarvisError as exc:
        return str(exc)
    return f"From {message.sender}, subject {message.subject}.\n\n{message.body[:4000]}"


@function_tool()
async def draft_email(
    context: RunContext, to: str, subject: str, body: str, cc: str | None = None
) -> str:
    """Create a Gmail draft. Always call this before send_email - never send directly.

    Args:
        to: Recipient email address.
        subject: Subject line.
        body: Plain text body.
        cc: Optional CC address.
    """
    try:
        draft_id = await asyncio.to_thread(gmail().create_draft, to, subject, body, cc)
    except JarvisError as exc:
        return str(exc)
    return (
        f"Draft {draft_id} created for {to}, subject '{subject}'. "
        "Read this back to the user and get explicit confirmation before sending."
    )


@function_tool()
async def send_email(context: RunContext, draft_id: str) -> str:
    """Send a previously created draft. Only call after the user has explicitly confirmed."""
    try:
        await asyncio.to_thread(gmail().send_draft, draft_id)
    except JarvisError as exc:
        return str(exc)
    return "Sent."


@function_tool()
async def archive_email(context: RunContext, message_id: str) -> str:
    """Remove a message from the inbox without deleting it."""
    try:
        await asyncio.to_thread(gmail().archive, message_id)
    except JarvisError as exc:
        return str(exc)
    return "Archived."


@function_tool()
async def trash_email(context: RunContext, message_id: str) -> str:
    """Move a message to trash. Recoverable for 30 days. Confirm with the user first."""
    try:
        await asyncio.to_thread(gmail().trash, message_id)
    except JarvisError as exc:
        return str(exc)
    return "Moved to trash."