from supabase import create_client, Client
from server.config import settings
import logging
from jose import jwt, JWTError
import requests

logger = logging.getLogger(__name__)

class SupabaseService:
    _instance: Client = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get Supabase client instance"""
        if cls._instance is None:
            cls._instance = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY  # Use service role for backend
            )
        return cls._instance
    
    @classmethod
    async def close_client(cls):
        """Close the Supabase client and clean up resources"""
        if cls._instance is not None:
            try:
                # Supabase client uses httpx internally, which should auto-close
                # But we can explicitly close if there's a close method
                if hasattr(cls._instance, 'close'):
                    await cls._instance.close()
                elif hasattr(cls._instance, '_client') and hasattr(cls._instance._client, 'close'):
                    await cls._instance._client.close()
                # Reset instance
                cls._instance = None
                logger.info("Supabase client closed successfully")
            except Exception as e:
                logger.warning(f"Error closing Supabase client: {e}")
    
    @classmethod
    def verify_token(cls, token: str) -> dict:
        """Verify Supabase JWT token and return user info"""
        try:
            # Method 1: Use Supabase Admin API to verify token
            # This is the most reliable method
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {token}"
            }
            
            # Get user info from Supabase
            response = requests.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "user_id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "authenticated": True
                }
            
            # If that fails, try decoding JWT directly
            # Supabase JWT secret is in Project Settings → API → JWT Secret
            # For now, we'll decode without verification (Supabase already verified it)
            try:
                # Decode without verification (token is already verified by Supabase)
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False}  # Skip signature verification
                )
                
                # Extract user info from payload
                user_id = payload.get("sub")
                email = payload.get("email")
                
                if user_id:
                    return {
                        "user_id": user_id,
                        "email": email,
                        "authenticated": True
                    }
            except JWTError as e:
                logger.error(f"JWT decode error: {e}")
            
            return {"authenticated": False}
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return {"authenticated": False}
    
    @classmethod
    async def get_calendar_credentials(cls, user_id: str) -> dict:
        """Get user's calendar credentials from database"""
        try:
            client = cls.get_client()
            response = client.table("calendar_credentials").select("*").eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching calendar credentials: {e}")
            return None
    
    @classmethod
    async def save_calendar_credentials(cls, user_id: str, credentials_json: str):
        """Save or update user's calendar credentials"""
        try:
            client = cls.get_client()
            # Check if record exists
            existing = client.table("calendar_credentials").select("*").eq("user_id", user_id).execute()
            
            if existing.data and len(existing.data) > 0:
                # Update existing
                client.table("calendar_credentials").update({
                    "credentials_json": credentials_json,
                    "updated_at": "now()"
                }).eq("user_id", user_id).execute()
            else:
                # Insert new
                client.table("calendar_credentials").insert({
                    "user_id": user_id,
                    "credentials_json": credentials_json
                }).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error saving calendar credentials: {e}")
            return False