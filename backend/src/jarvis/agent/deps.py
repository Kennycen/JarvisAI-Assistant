from __future__ import annotations

from functools import lru_cache

from jarvis.config import get_settings
from jarvis.core.browser import BrowserManager
from jarvis.core.connectors import DEFAULT_USER_ID
from jarvis.core.google.auth import FileTokenStore
from jarvis.core.google.calendar import CalendarService
from jarvis.core.google.gmail import GmailService
from jarvis.core.profile import FileProfileStore, Profile


@lru_cache
def _token_store(connector_id: str) -> FileTokenStore:
    return FileTokenStore(get_settings().token_dir, connector_id)


def gmail(user_id: str = DEFAULT_USER_ID) -> GmailService:
    return GmailService(user_id, _token_store("google-gmail"))


def calendar(user_id: str = DEFAULT_USER_ID) -> CalendarService:
    return CalendarService(user_id, _token_store("google-calendar"), get_settings().tzinfo)


def profile(user_id: str = DEFAULT_USER_ID) -> Profile:
    return FileProfileStore(get_settings().profile_dir).load(user_id)


@lru_cache
def browser() -> BrowserManager:
    """One browser for the whole worker process.

    Closing it resets it to an unstarted state, so the next session reopens it lazily.
    Multi-user will need one manager per room instead.
    """
    settings = get_settings()
    return BrowserManager(
        headless=settings.browser_headless,
        timeout_ms=settings.browser_timeout_ms,
    )
