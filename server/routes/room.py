from fastapi import APIRouter, HTTPException
from server.models.schemas import CreateRoomRequest, RoomResponse
from datetime import datetime
from server.models.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["room"])

@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint - doesn't require LiveKit"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat()
    )

@router.post("/create-room", response_model=RoomResponse)
async def create_room(request: CreateRoomRequest):
    """Create a LiveKit room and generate access token"""
    try:
        # Import only when needed, not at module level
        from server.services.livekit_service import get_livekit_service
        livekit_service = get_livekit_service()
        result = await livekit_service.create_room(request.participant_name)
        return RoomResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))