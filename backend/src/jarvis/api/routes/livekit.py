from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from livekit.api import AccessToken, VideoGrants
from livekit.protocol.agent_dispatch import RoomAgentDispatch
from livekit.protocol.room import RoomConfiguration
from pydantic import BaseModel, Field

from jarvis.config import Settings, get_settings

router = APIRouter(prefix="/livekit", tags=["livekit"])

AGENT_NAME = "jarvis"


class TokenRequest(BaseModel):
    identity: str = Field(default="kenny", max_length=64)
    room: str | None = None


class TokenResponse(BaseModel):
    server_url: str
    room: str
    token: str


@router.post("/token", response_model=TokenResponse)
def create_token(
    payload: TokenRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Mint a LiveKit join token for the frontend.

    Because the worker registers with agent_name, LiveKit will NOT auto-dispatch it.
    The RoomConfiguration below is what actually summons Jarvis into the room.
    Omit it and the frontend connects to a room where nobody is home.
    """
    room = payload.room or f"jarvis-{uuid.uuid4().hex[:8]}"

    token = (
        AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(payload.identity)
        .with_name(payload.identity)
        .with_grants(
            VideoGrants(room_join=True, room=room, can_publish=True, can_subscribe=True)
        )
        .with_room_config(
            RoomConfiguration(agents=[RoomAgentDispatch(agent_name=AGENT_NAME)])
        )
        .with_ttl(timedelta(hours=6))
    )

    return TokenResponse(server_url=settings.livekit_url, room=room, token=token.to_jwt())