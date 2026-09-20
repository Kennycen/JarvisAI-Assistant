from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from google.oauth2.credentials import Credentials

from jarvis.config import Settings
from jarvis.core.connectors import get_connector
from jarvis.core.google.auth import FileTokenStore
from jarvis.core.google.oauth import redirect_uri


def _credentials() -> Credentials:
    return Credentials(
        token="ya29.token",
        refresh_token="1//refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="cid",
        client_secret="csecret",
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
        expiry=datetime.now(UTC) + timedelta(hours=1),
    )


def test_list_connectors_reports_disconnected_by_default(client) -> None:
    rows = client.get("/api/connectors").json()
    by_id = {row["id"]: row for row in rows}
    assert by_id["google-gmail"]["status"] == "disconnected"
    assert by_id["google-gmail"]["available"] is True
    assert by_id["slack"]["status"] == "unavailable"
    assert by_id["slack"]["available"] is False


def test_list_connectors_reflects_a_saved_token(client, tmp_settings: Settings) -> None:
    FileTokenStore(tmp_settings.token_dir, "google-gmail").save("local", _credentials())
    rows = client.get("/api/connectors").json()
    gmail = next(row for row in rows if row["id"] == "google-gmail")
    calendar = next(row for row in rows if row["id"] == "google-calendar")
    assert gmail["status"] == "connected"
    assert calendar["status"] == "disconnected"


def test_connect_unknown_connector_is_404(client) -> None:
    assert client.post("/api/connectors/nope/connect").status_code == 404


def test_connect_placeholder_is_400(client) -> None:
    res = client.post("/api/connectors/slack/connect")
    assert res.status_code == 400
    assert "not available" in res.json()["detail"]


def test_connect_returns_google_consent_url_with_offline_access(client) -> None:
    res = client.post("/api/connectors/google-gmail/connect")
    assert res.status_code == 200
    url = res.json()["authorization_url"]
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert parsed.netloc.endswith("google.com")
    assert "https://www.googleapis.com/auth/gmail.modify" in query["scope"][0]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]
    assert "state" in query
    assert query["redirect_uri"] == [
        "http://localhost:8000/api/connectors/google-gmail/callback"
    ]


def test_gmail_and_calendar_redirect_uris_are_distinct(tmp_settings: Settings) -> None:
    gmail = redirect_uri(get_connector("google-gmail"), tmp_settings)
    calendar = redirect_uri(get_connector("google-calendar"), tmp_settings)
    assert gmail.endswith("/api/connectors/google-gmail/callback")
    assert calendar.endswith("/api/connectors/google-calendar/callback")
    assert gmail != calendar


def test_callback_without_state_returns_expired_html(client) -> None:
    res = client.get("/api/connectors/google-gmail/callback")
    assert res.status_code == 200
    assert "Authorization expired" in res.text
    assert "jarvis-oauth" in res.text


def test_callback_restores_the_pkce_verifier(client, monkeypatch) -> None:
    """Google rejects the token exchange if the rebuilt Flow has no code_verifier."""
    captured: dict[str, str | None] = {}

    def fake_exchange(flow, authorization_response: str):
        captured["verifier"] = flow.code_verifier
        captured["response"] = authorization_response
        return _credentials()

    monkeypatch.setattr("jarvis.api.routes.connectors.oauth.exchange_code", fake_exchange)
    monkeypatch.setattr(
        "jarvis.api.routes.connectors.oauth.fetch_account",
        lambda spec, creds: "kenny@example.com",
    )

    start = client.post("/api/connectors/google-gmail/connect")
    query = parse_qs(urlparse(start.json()["authorization_url"]).query)
    state = query["state"][0]
    assert query.get("code_challenge"), "consent URL must use PKCE"

    res = client.get(
        "/api/connectors/google-gmail/callback",
        params={"state": state, "code": "fake-code"},
    )
    assert res.status_code == 200
    assert "Connected" in res.text
    assert captured.get("verifier"), "callback must restore the PKCE verifier from Connect"


def test_disconnect_unknown_connector_is_404(client) -> None:
    assert client.delete("/api/connectors/nope").status_code == 404


def test_disconnect_without_a_token_is_idempotent(client) -> None:
    res = client.delete("/api/connectors/google-gmail")
    assert res.status_code == 200
    assert res.json()["status"] == "disconnected"


def test_disconnect_deletes_the_token_file(client, tmp_settings: Settings) -> None:
    store = FileTokenStore(tmp_settings.token_dir, "google-gmail")
    store.save("local", _credentials())
    assert store.load("local") is not None

    res = client.delete("/api/connectors/google-gmail")
    assert res.status_code == 200
    assert res.json()["status"] == "disconnected"
    assert store.load("local") is None
    assert not list(Path(tmp_settings.token_dir).glob("*.meta.json"))
