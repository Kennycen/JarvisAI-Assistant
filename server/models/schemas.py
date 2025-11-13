from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Room Management
class CreateRoomRequest(BaseModel):
    participant_name: str = "user"

class RoomResponse(BaseModel):
    room_name: str
    token: str
    url: str

# Health Check
class HealthResponse(BaseModel):
    status: str
    timestamp: str

# OAuth
class AuthStatusResponse(BaseModel):
    authenticated: bool
    email: Optional[str] = None