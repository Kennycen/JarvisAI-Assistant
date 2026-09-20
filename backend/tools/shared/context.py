"""Room context management for tools"""
from typing import Optional
from livekit.agents import RunContext
from tools.room_context import get_current_room_name

def get_room_name(context: Optional[RunContext] = None) -> Optional[str]:
    """
    Get room name from multiple sources with priority:
    1. Global storage (most reliable)
    2. Context object
    
    Args:
        context: LiveKit agent context (optional)
        
    Returns:
        Room name if found, None otherwise
    """
    # Priority 1: Global storage
    room_name = get_current_room_name()
    if room_name:
        return room_name
    
    # Priority 2: Context object
    if context:
        try:
            if hasattr(context, 'room') and hasattr(context.room, 'name'):
                return context.room.name
            elif hasattr(context, 'room_name'):
                return context.room_name
        except Exception:
            pass
    
    return None