# Base class for all tools
from abc import ABC, abstractmethod
from typing import Optional
from livekit.agents import RunContext
from tools.shared.context import get_room_name
from tools.shared.database import get_user_id_from_room
from tools.shared.errors import ToolError

class BaseTool(ABC):
    """Base class for all JARVIS tools"""
    
    def __init__(self, context: Optional[RunContext] = None):
        self.context = context
        self._room_name: Optional[str] = None
        self._user_id: Optional[str] = None
    
    @property
    def room_name(self) -> Optional[str]:
        # Get room name, caching result
        if self._room_name is None:
            self._room_name = get_room_name(self.context)
        return self._room_name
    
    @property
    def user_id(self) -> Optional[str]:
        # Get user ID, caching result
        if self._user_id is None and self.room_name:
            self._user_id = get_user_id_from_room(self.room_name)
        return self._user_id
    
    def validate_auth(self) -> None:
        # Validate that authentication is available
        if not self.user_id:
            raise ToolError("User authentication required. Please connect your account.")
    
    @abstractmethod
    async def execute(self, *args, **kwargs):
        # Execute the tool - must be implemented by subclasses
        pass