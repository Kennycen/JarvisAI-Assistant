from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from server.services.supabase_service import SupabaseService
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify JWT token and return current user"""
    token = credentials.credentials
    
    # Supabase tokens are JWT, verify them
    user_info = SupabaseService.verify_token(token)
    
    if not user_info.get("authenticated"):
        logger.warning(f"Token verification failed for token: {token[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info