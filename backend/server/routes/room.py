from fastapi import APIRouter, HTTPException, Depends
from server.models.schemas import CreateRoomRequest, RoomResponse
from server.services.livekit_service import get_livekit_service
from server.middleware.auth import get_current_user
from server.services.supabase_service import SupabaseService
from datetime import datetime
from server.models.schemas import HealthResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["room"])

@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint - doesn't require authentication"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat()
    )

@router.post("/create-room", response_model=RoomResponse)
async def create_room(
    request: CreateRoomRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a LiveKit room and generate access token"""
    try:
        livekit_service = get_livekit_service()
        result = await livekit_service.create_room(request.participant_name)
        
        # Save room to Supabase linked to user
        client = SupabaseService.get_client()
        client.table("rooms").insert({
            "user_id": current_user["user_id"],
            "room_name": result["room_name"]
        }).execute()
        
        return RoomResponse(**result)
    except Exception as e:
        logger.error(f"Error creating room: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))