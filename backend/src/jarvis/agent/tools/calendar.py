from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from livekit.agents import RunContext, function_tool

from jarvis.agent.deps import calendar
from jarvis.config import get_settings
from jarvis.core.errors import JarvisError


@function_tool()
async def list_events(context: RunContext, days_ahead: int = 7) -> str:
    """List upcoming calendar events.

    Args:
        days_ahead: How many days forward to look.
    """
    try:
        events = await asyncio.to_thread(calendar().list_events, days_ahead)
    except JarvisError as exc:
        return str(exc)

    if not events:
        return f"Nothing scheduled in the next {days_ahead} days."

    return "\n".join(
        f"[{e.id}] {e.summary} starting {e.start}" + (f" at {e.location}" if e.location else "")
        for e in events
    )


@function_tool()
async def create_event(
    context: RunContext,
    summary: str,
    start_iso: str,
    duration_minutes: int = 60,
    description: str = "",
    location: str = "",
) -> str:
    """Create a calendar event.

    Args:
        summary: Event title.
        start_iso: Start time as ISO 8601 local time, e.g. "2026-09-24T15:00:00".
        duration_minutes: Length of the event in minutes.
        description: Optional notes.
        location: Optional location.
    """
    try:
        start = datetime.fromisoformat(start_iso)
    except ValueError:
        return f"'{start_iso}' is not a valid date and time."

    if start.tzinfo is None:
        start = start.replace(tzinfo=get_settings().tzinfo)

    try:
        event = await asyncio.to_thread(
            calendar().create_event,
            summary,
            start,
            start + timedelta(minutes=duration_minutes),
            description,
            location,
        )
    except JarvisError as exc:
        return str(exc)

    return f"Created '{event.summary}' starting {event.start}."


@function_tool()
async def delete_event(context: RunContext, event_id: str) -> str:
    """Delete a calendar event. Confirm with the user before calling this."""
    try:
        await asyncio.to_thread(calendar().delete_event, event_id)
    except JarvisError as exc:
        return str(exc)
    return "Deleted."