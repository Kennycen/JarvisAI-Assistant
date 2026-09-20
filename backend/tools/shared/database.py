"""Shared database utilities for all tools"""
import os
import logging
from typing import Optional
from functools import lru_cache
from supabase import create_client, Client
from tools.shared.errors import ConfigurationError

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Get Supabase client singleton (cached).
    
    Returns:
        Supabase client instance
        
    Raises:
        ConfigurationError: If credentials are missing
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ConfigurationError(
            "Supabase credentials not found. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in environment."
        )
    
    return create_client(supabase_url, supabase_key)

def get_user_id_from_room(room_name: str) -> Optional[str]:
    """
    Get user_id from room name.
    
    Args:
        room_name: The LiveKit room name
        
    Returns:
        User ID if found, None otherwise
    """
    if not room_name:
        return None
        
    try:
        client = get_supabase_client()
        response = client.table("rooms").select("user_id").eq("room_name", room_name).execute()
        
        if response.data and len(response.data) > 0:
            user_id = response.data[0]["user_id"]
            logger.debug(f"Found user_id: {user_id} for room: {room_name}")
            return user_id
        
        logger.warning(f"No user found for room: {room_name}")
        return None
    except Exception as e:
        logger.error(f"Error getting user from room {room_name}: {e}", exc_info=True)
        return None