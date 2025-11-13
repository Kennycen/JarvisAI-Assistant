import secrets
import logging
from server.config import settings

# Try to import LiveKit API with fallbacks
try:
    from livekit import api
    LIVEKIT_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import livekit.api: {e}")
    LIVEKIT_AVAILABLE = False
    api = None

logger = logging.getLogger(__name__)

class LiveKitService:
    def __init__(self):
        if not LIVEKIT_AVAILABLE:
            raise ImportError("LiveKit API is not available. Check your installation.")
        
        # Validate settings
        if not settings.LIVEKIT_URL or not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
            raise ValueError("LiveKit credentials are missing. Check your .env file.")
        
        try:
            # Try different API patterns
            if hasattr(api, 'LiveKitAPI'):
                self.lk_api = api.LiveKitAPI(
                    url=settings.LIVEKIT_URL,
                    api_key=settings.LIVEKIT_API_KEY,
                    api_secret=settings.LIVEKIT_API_SECRET
                )
            elif hasattr(api, 'room_service'):
                # Alternative pattern
                self.lk_api = api.room_service.RoomService(
                    settings.LIVEKIT_URL,
                    settings.LIVEKIT_API_KEY,
                    settings.LIVEKIT_API_SECRET
                )
            else:
                # Last resort - check what's available
                available = [x for x in dir(api) if not x.startswith('_')]
                raise AttributeError(
                    f"Could not find LiveKitAPI or room_service. "
                    f"Available in api: {available}"
                )
        except Exception as e:
            logger.error(f"Failed to initialize LiveKit API: {e}")
            raise
    
    async def create_room(self, participant_name: str = "user"):
        """Create a LiveKit room and generate access token"""
        try:
            # Generate unique room name
            room_name = f"room_{secrets.token_urlsafe(8)}"
            
            # Create room - try different patterns
            try:
                if hasattr(self.lk_api, 'room'):
                    # Pattern: lk_api.room.create_room()
                    room = await self.lk_api.room.create_room(
                        api.CreateRoomRequest(name=room_name)
                    )
                else:
                    # Pattern: lk_api.create_room()
                    room = await self.lk_api.create_room(
                        api.CreateRoomRequest(name=room_name)
                    )
            except AttributeError:
                # Try with dict
                room = await self.lk_api.create_room({"name": room_name})
            
            # Generate access token - try different import paths
            try:
                if hasattr(api, 'AccessToken'):
                    token = api.AccessToken(
                        settings.LIVEKIT_API_KEY,
                        settings.LIVEKIT_API_SECRET
                    ).with_identity(participant_name) \
                     .with_name(participant_name) \
                     .with_grants(api.VideoGrants(
                         room_join=True,
                         room=room_name,
                         can_publish=True,
                         can_subscribe=True,
                     )).to_jwt()
                else:
                    from livekit import AccessToken, VideoGrants
                    token = AccessToken(
                        settings.LIVEKIT_API_KEY,
                        settings.LIVEKIT_API_SECRET
                    ).with_identity(participant_name) \
                     .with_name(participant_name) \
                     .with_grants(VideoGrants(
                         room_join=True,
                         room=room_name,
                         can_publish=True,
                         can_subscribe=True,
                     )).to_jwt()
            except Exception as token_error:
                logger.error(f"Failed to generate token: {token_error}")
                raise Exception(f"Token generation failed: {token_error}")
            
            return {
                "room_name": room_name,
                "token": token,
                "url": settings.LIVEKIT_URL
            }
        except Exception as e:
            logger.error(f"Failed to create room: {e}")
            raise Exception(f"Failed to create room: {str(e)}")

# Create instance on demand to avoid import-time initialization
def get_livekit_service():
    return LiveKitService()