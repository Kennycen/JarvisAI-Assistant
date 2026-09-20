from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials

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


def test_token_path_includes_connector_id(tmp_path: Path) -> None:
    store = FileTokenStore(tmp_path, "google-gmail")
    store.save("local", _credentials())
    assert (tmp_path / "local-google-gmail.json").exists()
    assert not (tmp_path / "local.json").exists()


def test_gmail_and_calendar_tokens_do_not_overwrite_each_other(tmp_path: Path) -> None:
    gmail = FileTokenStore(tmp_path, "google-gmail")
    calendar = FileTokenStore(tmp_path, "google-calendar")
    gmail.save("local", _credentials(refresh_token="gmail"))
    calendar.save("local", _credentials(refresh_token="calendar"))

    assert gmail.load("local").refresh_token == "gmail"
    assert calendar.load("local").refresh_token == "calendar"


def test_load_missing_token_returns_none(tmp_path: Path) -> None:
    assert FileTokenStore(tmp_path, "google-gmail").load("local") is None


def test_delete_removes_only_that_connector(tmp_path: Path) -> None:
    gmail = FileTokenStore(tmp_path, "google-gmail")
    calendar = FileTokenStore(tmp_path, "google-calendar")
    gmail.save("local", _credentials())
    calendar.save("local", _credentials())

    gmail.delete("local")

    assert gmail.load("local") is None
    assert calendar.load("local") is not None


def test_delete_missing_token_is_silent(tmp_path: Path) -> None:
    FileTokenStore(tmp_path, "google-gmail").delete("local")


def test_load_tolerates_missing_refresh_token(tmp_path: Path) -> None:
    store = FileTokenStore(tmp_path, "google-gmail")
    store.save("local", _credentials(refresh_token=None, expired=True))
    loaded = store.load("local")
    assert loaded is not None
    assert loaded.refresh_token is None
    assert loaded.expired is True
