from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from jarvis.core.errors import AuthenticationError

logger = logging.getLogger(__name__)


def _parse_expiry(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    # Google's to_json sometimes emits a trailing Z on top of an offset.
    cleaned = raw.rstrip("Z")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    # google-auth compares expiry to a naive UTC now().
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed


class TokenStore(Protocol):
    def load(self, user_id: str) -> Credentials | None: ...
    def save(self, user_id: str, credentials: Credentials) -> None: ...
    def delete(self, user_id: str) -> None: ...


class FileTokenStore:
    """One token file per user *per connector* on local disk.

    Keeping Gmail and Calendar in separate grants is what lets the sidebar
    connect and disconnect them independently.

    Moving to Supabase later means writing a second class that satisfies
    TokenStore. No caller changes.
    """

    def __init__(self, directory: Path, connector_id: str) -> None:
        self._directory = directory
        self._connector_id = connector_id

    def _path(self, user_id: str) -> Path:
        return self._directory / f"{user_id}-{self._connector_id}.json"

    def load(self, user_id: str) -> Credentials | None:
        path = self._path(user_id)
        if not path.exists():
            return None
        info = json.loads(path.read_text())
        try:
            # No explicit scope list: each grant carries the scopes it was issued.
            return Credentials.from_authorized_user_info(info)
        except ValueError:
            # Google's helper requires a refresh_token field. An access-token-only
            # file is still a real (just unrenewable) connection.
            if not info.get("token"):
                raise
            expiry_raw = info.get("expiry")
            expiry = _parse_expiry(expiry_raw)
            return Credentials(
                token=info.get("token"),
                refresh_token=info.get("refresh_token"),
                token_uri=info.get("token_uri") or "https://oauth2.googleapis.com/token",
                client_id=info.get("client_id"),
                client_secret=info.get("client_secret"),
                scopes=info.get("scopes"),
                expiry=expiry,
            )

    def save(self, user_id: str, credentials: Credentials) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._path(user_id)
        path.write_text(credentials.to_json())
        path.chmod(0o600)

    def delete(self, user_id: str) -> None:
        self._path(user_id).unlink(missing_ok=True)


def get_credentials(user_id: str, store: TokenStore) -> Credentials:
    credentials = store.load(user_id)
    if credentials is None:
        raise AuthenticationError(
            "That account is not connected. Open the Connectors section "
            "in the Jarvis sidebar and link it."
        )

    if credentials.expired:
        if not credentials.refresh_token:
            raise AuthenticationError("Google session expired and cannot refresh. Re-authorize.")
        logger.info("Refreshing Google credentials for %s", user_id)
        credentials.refresh(Request())
        store.save(user_id, credentials)

    return credentials


def build_service(api: str, version: str, user_id: str, store: TokenStore) -> Any:
    credentials = get_credentials(user_id, store)
    return build(api, version, credentials=credentials, cache_discovery=False)