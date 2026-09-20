from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from jarvis.api.routes import connectors, profile
from jarvis.config import Settings, get_settings

WEB_CLIENT_SECRET = {
    "web": {
        "client_id": "test.apps.googleusercontent.com",
        "project_id": "test",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_secret": "test-secret",
        "redirect_uris": [
            "http://localhost:8000/api/connectors/google-gmail/callback",
            "http://localhost:8000/api/connectors/google-calendar/callback",
        ],
    }
}


@pytest.fixture
def tmp_settings(tmp_path: Path) -> Settings:
    secrets = tmp_path / "client_secret.json"
    secrets.write_text(json.dumps(WEB_CLIENT_SECRET))
    return Settings(
        google_api_key="test",
        livekit_url="wss://example.livekit.cloud",
        livekit_api_key="key",
        livekit_api_secret="secret",
        client_secrets_file=secrets,
        token_dir=tmp_path / "tokens",
        data_dir=tmp_path / "data",
        public_api_url="http://localhost:8000",
        cors_origins=["http://localhost:3000"],
    )


@pytest.fixture
def client(tmp_settings: Settings) -> TestClient:
    app = FastAPI()
    app.include_router(connectors.router, prefix="/api")
    app.include_router(profile.router, prefix="/api")
    app.dependency_overrides[get_settings] = lambda: tmp_settings
    return TestClient(app)
