from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """All configuration, validated once at startup.

    Pydantic raises a clear error on boot if a required variable is missing,
    rather than failing with an AttributeError deep inside a tool call.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_api_key: str
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str

    jarvis_timezone: str = "America/New_York"
    log_level: str = "INFO"

    # A visible window lets the user watch Jarvis browse. Set true when running headless
    # in a container, where no display is available.
    browser_headless: bool = False
    browser_timeout_ms: int = 15_000

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Where the browser can reach this API. OAuth redirect URIs are built from it,
    # so it must match what is registered in Google Cloud Console exactly.
    public_api_url: str = "http://localhost:8000"

    client_secrets_file: Path = PROJECT_ROOT / "secrets" / "client_secret.json"
    token_dir: Path = PROJECT_ROOT / "secrets" / "tokens"
    # Personal but not secret, so it lives outside secrets/.
    data_dir: Path = PROJECT_ROOT / "data"

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.jarvis_timezone)

    @property
    def profile_dir(self) -> Path:
        return self.data_dir / "profile"

    @property
    def frontend_origin(self) -> str:
        """Target origin for the OAuth popup's postMessage back to the HUD."""
        return self.cors_origins[0]


@lru_cache
def get_settings() -> Settings:
    return Settings()