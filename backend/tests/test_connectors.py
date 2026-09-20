from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials

from jarvis.core.connectors import CONNECTORS, MetaStore, get_connector, read_all, read_state
from jarvis.core.google.auth import FileTokenStore


def _credentials(*, refresh_token: str | None = "1//refresh", expired: bool = False) -> Credentials:
    if expired:
        expiry = datetime.now(UTC) - timedelta(hours=1)
    else:
        expiry = datetime.now(UTC) + timedelta(hours=1)
    return Credentials(
        token="ya29.token",
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id="cid",
        client_secret="csecret",
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
        expiry=expiry,
    )


def test_registry_includes_live_google_connectors_and_placeholders() -> None:
    ids = {spec.id for spec in CONNECTORS}
    assert {"google-gmail", "google-calendar", "slack", "notion", "github", "home-assistant"} <= ids
    assert get_connector("google-gmail").available is True
    assert get_connector("slack").available is False
    assert get_connector("nope") is None


def test_placeholder_is_unavailable_even_with_a_token_file(tmp_path: Path) -> None:
    slack = get_connector("slack")
    FileTokenStore(tmp_path, slack.id).save("local", _credentials())
    state = read_state(slack, "local", tmp_path)
    assert state.status == "unavailable"


def test_missing_token_is_disconnected(tmp_path: Path) -> None:
    state = read_state(get_connector("google-gmail"), "local", tmp_path)
    assert state.status == "disconnected"
    assert state.account is None


def test_valid_token_is_connected_and_exposes_account_metadata(tmp_path: Path) -> None:
    spec = get_connector("google-gmail")
    FileTokenStore(tmp_path, spec.id).save("local", _credentials())
    MetaStore(tmp_path).save("local", spec.id, "kenny@example.com")

    state = read_state(spec, "local", tmp_path)
    assert state.status == "connected"
    assert state.account == "kenny@example.com"
    assert state.connected_at is not None


def test_expired_token_without_refresh_is_expired(tmp_path: Path) -> None:
    spec = get_connector("google-gmail")
    FileTokenStore(tmp_path, spec.id).save(
        "local", _credentials(refresh_token=None, expired=True)
    )
    state = read_state(spec, "local", tmp_path)
    assert state.status == "expired"


def test_expired_token_with_refresh_is_still_connected(tmp_path: Path) -> None:
    spec = get_connector("google-gmail")
    FileTokenStore(tmp_path, spec.id).save(
        "local", _credentials(refresh_token="1//still-good", expired=True)
    )
    state = read_state(spec, "local", tmp_path)
    assert state.status == "connected"


def test_read_all_covers_every_registry_entry(tmp_path: Path) -> None:
    states = read_all("local", tmp_path)
    assert [s.spec.id for s in states] == [spec.id for spec in CONNECTORS]


def test_meta_store_delete_is_idempotent(tmp_path: Path) -> None:
    store = MetaStore(tmp_path)
    store.save("local", "google-gmail", "a@b.com")
    store.delete("local", "google-gmail")
    store.delete("local", "google-gmail")
    assert store.load("local", "google-gmail").account is None
