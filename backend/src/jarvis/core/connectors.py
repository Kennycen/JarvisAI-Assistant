"""The catalogue of third-party integrations and how to read their state.

One spec per connector drives everything downstream: the scopes requested during
authorization, the token filename, and the row the sidebar renders. Adding a
provider means adding a tuple entry plus an OAuth implementation for it.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from jarvis.core.google.auth import FileTokenStore

logger = logging.getLogger(__name__)

# Phase 1 is single-user. When multi-user arrives this becomes the room's user id
# and nothing else about the storage layer changes.
DEFAULT_USER_ID = "local"

Provider = Literal["google", "placeholder"]
ConnectorStatus = Literal["connected", "disconnected", "expired", "unavailable"]


@dataclass(frozen=True)
class ConnectorSpec:
    id: str
    name: str
    description: str
    category: str
    provider: Provider
    scopes: tuple[str, ...] = ()
    # False means the UI shows the row greyed out; there is no backend for it yet.
    available: bool = True


CONNECTORS: tuple[ConnectorSpec, ...] = (
    ConnectorSpec(
        id="google-gmail",
        name="Gmail",
        description="Search, read, draft, send and archive mail",
        category="Google",
        provider="google",
        scopes=("https://www.googleapis.com/auth/gmail.modify",),
    ),
    ConnectorSpec(
        id="google-calendar",
        name="Google Calendar",
        description="List, create and delete events",
        category="Google",
        provider="google",
        scopes=("https://www.googleapis.com/auth/calendar",),
    ),
    ConnectorSpec(
        id="slack",
        name="Slack",
        description="Read channels and post messages",
        category="Messaging",
        provider="placeholder",
        available=False,
    ),
    ConnectorSpec(
        id="notion",
        name="Notion",
        description="Search pages and append to databases",
        category="Knowledge",
        provider="placeholder",
        available=False,
    ),
    ConnectorSpec(
        id="github",
        name="GitHub",
        description="Track issues, pull requests and CI",
        category="Development",
        provider="placeholder",
        available=False,
    ),
    ConnectorSpec(
        id="home-assistant",
        name="Home Assistant",
        description="Control lights, climate and scenes",
        category="Home",
        provider="placeholder",
        available=False,
    ),
)

_BY_ID = {spec.id: spec for spec in CONNECTORS}


def get_connector(connector_id: str) -> ConnectorSpec | None:
    return _BY_ID.get(connector_id)


@dataclass(frozen=True)
class ConnectionMeta:
    """Non-secret facts about a connection, shown in the sidebar."""

    account: str | None = None
    connected_at: str | None = None


class MetaStore:
    """Sits beside the token files; holds nothing worth protecting."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def _path(self, user_id: str, connector_id: str) -> Path:
        return self._directory / f"{user_id}-{connector_id}.meta.json"

    def load(self, user_id: str, connector_id: str) -> ConnectionMeta:
        path = self._path(user_id, connector_id)
        if not path.exists():
            return ConnectionMeta()
        try:
            raw = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            logger.warning("Unreadable connector metadata at %s", path)
            return ConnectionMeta()
        return ConnectionMeta(account=raw.get("account"), connected_at=raw.get("connected_at"))

    def save(self, user_id: str, connector_id: str, account: str | None) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        self._path(user_id, connector_id).write_text(
            json.dumps(
                {"account": account, "connected_at": datetime.now(UTC).isoformat()},
                indent=2,
            )
        )

    def delete(self, user_id: str, connector_id: str) -> None:
        self._path(user_id, connector_id).unlink(missing_ok=True)


@dataclass(frozen=True)
class ConnectorState:
    spec: ConnectorSpec
    status: ConnectorStatus
    account: str | None = None
    connected_at: str | None = None


def read_state(spec: ConnectorSpec, user_id: str, token_dir: Path) -> ConnectorState:
    """Derive status from what is on disk rather than trusting a stored flag."""
    if not spec.available:
        return ConnectorState(spec, "unavailable")

    try:
        credentials = FileTokenStore(token_dir, spec.id).load(user_id)
    except Exception:
        logger.warning("Corrupt token for %s; treating as disconnected", spec.id, exc_info=True)
        return ConnectorState(spec, "disconnected")

    if credentials is None:
        return ConnectorState(spec, "disconnected")

    meta = MetaStore(token_dir).load(user_id, spec.id)
    # An expired token with a refresh token is routine; it renews on next use.
    status: ConnectorStatus = (
        "expired" if credentials.expired and not credentials.refresh_token else "connected"
    )
    return ConnectorState(spec, status, meta.account, meta.connected_at)


def read_all(user_id: str, token_dir: Path) -> list[ConnectorState]:
    return [read_state(spec, user_id, token_dir) for spec in CONNECTORS]
