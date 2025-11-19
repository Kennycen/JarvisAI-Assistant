# tools/room_context.py
"""Shared room context for tools"""

_current_room_name = None

def set_current_room_name(room_name: str):
    """Set the current room name"""
    global _current_room_name
    _current_room_name = room_name

def get_current_room_name():
    """Get the current room name"""
    return _current_room_name