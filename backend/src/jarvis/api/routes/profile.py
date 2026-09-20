from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from jarvis.config import Settings, get_settings
from jarvis.core.connectors import DEFAULT_USER_ID
from jarvis.core.profile import FileProfileStore, Profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


def _store(settings: Settings) -> FileProfileStore:
    return FileProfileStore(settings.profile_dir)


@router.get("", response_model=Profile)
def read_profile(settings: Annotated[Settings, Depends(get_settings)]) -> Profile:
    return _store(settings).load(DEFAULT_USER_ID)


@router.put("", response_model=Profile)
def write_profile(
    profile: Profile,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Profile:
    """Takes effect on the next session - the worker reads this when it builds
    the agent, not while one is running."""
    _store(settings).save(DEFAULT_USER_ID, profile)
    logger.info("Profile updated")
    return profile
