"""Browser-driven Google authorization.

The CLI flow this replaces used InstalledAppFlow, which spins up its own
throwaway web server. Here the API *is* the web server, so the redirect comes
back to a real route and the frontend only has to open a popup.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any
from urllib.parse import urlencode, urlparse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from jarvis.config import Settings
from jarvis.core.connectors import ConnectorSpec
from jarvis.core.errors import AuthenticationError

logger = logging.getLogger(__name__)

REVOKE_URL = "https://oauth2.googleapis.com/revoke"

# Google returns granted scopes in its own order and sometimes adds to them,
# which oauthlib treats as a mismatch and raises on. We request one scope per
# connector deliberately, so relaxing this check costs nothing.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")


def redirect_uri(spec: ConnectorSpec, settings: Settings) -> str:
    return f"{settings.public_api_url.rstrip('/')}/api/connectors/{spec.id}/callback"


def _allow_insecure_transport(uri: str) -> None:
    """oauthlib refuses plain-HTTP redirects, which would block all local dev.

    Only loosened for loopback addresses; a deployed http:// origin should fail.
    """
    host = urlparse(uri).hostname
    if host in {"localhost", "127.0.0.1", "::1"}:
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def build_flow(spec: ConnectorSpec, settings: Settings, state: str | None = None) -> Flow:
    if not settings.client_secrets_file.exists():
        raise AuthenticationError(
            f"Missing {settings.client_secrets_file}. Download an OAuth client "
            "from Google Cloud Console and save it there."
        )

    uri = redirect_uri(spec, settings)
    _allow_insecure_transport(uri)

    return Flow.from_client_secrets_file(
        str(settings.client_secrets_file),
        scopes=list(spec.scopes),
        redirect_uri=uri,
        state=state,
    )


def authorization_url(flow: Flow) -> tuple[str, str]:
    url, state = flow.authorization_url(
        # Without offline+consent Google withholds the refresh token on repeat
        # authorizations, and the connection silently dies after an hour.
        access_type="offline",
        prompt="consent",
        # Incremental auth would fold Gmail's scope into Calendar's grant and
        # make the two connectors inseparable again.
        include_granted_scopes="false",
    )
    return url, state


def exchange_code(flow: Flow, authorization_response: str) -> Credentials:
    flow.fetch_token(authorization_response=authorization_response)
    return flow.credentials


# Each Google API can name its own account, which avoids asking for the extra
# userinfo.email scope just to render "connected as ...".
_ACCOUNT_PROBES: dict[str, Callable[[Any], str | None]] = {
    "google-gmail": lambda service: service.users().getProfile(userId="me").execute().get(
        "emailAddress"
    ),
    "google-calendar": lambda service: service.calendarList()
    .get(calendarId="primary")
    .execute()
    .get("id"),
}

_APIS: dict[str, tuple[str, str]] = {
    "google-gmail": ("gmail", "v1"),
    "google-calendar": ("calendar", "v3"),
}


def fetch_account(spec: ConnectorSpec, credentials: Credentials) -> str | None:
    """Best effort. A failure here must not fail an otherwise good connection."""
    probe = _ACCOUNT_PROBES.get(spec.id)
    api = _APIS.get(spec.id)
    if probe is None or api is None:
        return None
    try:
        service = build(api[0], api[1], credentials=credentials, cache_discovery=False)
        return probe(service)
    except Exception:
        logger.warning("Could not read the account name for %s", spec.id, exc_info=True)
        return None


def revoke(credentials: Credentials) -> None:
    """Tell Google to drop the grant. Never raises - the caller deletes locally
    either way, and a stranded remote grant is better than an undeletable row."""
    token = credentials.refresh_token or credentials.token
    if not token:
        return
    try:
        Request()(
            url=REVOKE_URL,
            method="POST",
            body=urlencode({"token": token}).encode(),
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
    except Exception:
        logger.warning("Google token revocation failed; removing local token anyway")
