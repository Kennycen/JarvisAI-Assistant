from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    DATABASE_URL: str = ""
    SUPABASE_DB_PASSWORD: str = "" 
    
    # FastAPI
    SECRET_KEY: str = "your-secret-key-change-in-production"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # LiveKit
    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""
    
    # Gmail
    GMAIL_USER: str = ""
    GMAIL_APP_PASSWORD: str = ""
    
    # Google API
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLOUD_PROJECT_ID: str = ""
    GOOGLE_CLIENT_ID: str = ""  # Add missing field
    GOOGLE_CLIENT_SECRET: str = ""  # Add missing field
    OAUTH_REDIRECT_URI: str = ""
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js dev server
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra fields in .env that aren't in this class
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add FRONTEND_URL to CORS_ORIGINS if not already present
        if self.FRONTEND_URL and self.FRONTEND_URL not in self.CORS_ORIGINS:
            self.CORS_ORIGINS.append(self.FRONTEND_URL)

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

settings = get_settings()