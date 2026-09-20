"""What Jarvis knows about the person he works for.

Deliberately mostly prose. The profile is destined for a system prompt, and
over-structuring it buys nothing a language model can use.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Profile(BaseModel):
    preferred_name: str = Field(default="", max_length=80)
    location: str = Field(default="", max_length=120)
    occupation: str = Field(default="", max_length=200)
    # Bounded so the profile can never crowd out the rest of the prompt.
    about: str = Field(default="", max_length=4000)
    preferences: str = Field(default="", max_length=2000)

    @property
    def is_empty(self) -> bool:
        return not any(
            value.strip()
            for value in (
                self.preferred_name,
                self.location,
                self.occupation,
                self.about,
                self.preferences,
            )
        )


class ProfileStore(Protocol):
    def load(self, user_id: str) -> Profile: ...
    def save(self, user_id: str, profile: Profile) -> None: ...


class FileProfileStore:
    """One JSON file per user. Swapping in Supabase is a second class here."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def _path(self, user_id: str) -> Path:
        return self._directory / f"{user_id}.json"

    def load(self, user_id: str) -> Profile:
        path = self._path(user_id)
        if not path.exists():
            return Profile()
        try:
            return Profile.model_validate_json(path.read_text())
        except (OSError, ValueError):
            # A malformed profile should never stop a session from starting.
            logger.warning("Unreadable profile at %s; using an empty one", path)
            return Profile()

    def save(self, user_id: str, profile: Profile) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        self._path(user_id).write_text(json.dumps(profile.model_dump(), indent=2))
