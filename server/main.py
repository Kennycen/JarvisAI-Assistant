from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from server.config import settings
from server.routes import room, auth
from server.services.supabase_service import SupabaseService
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="JARVIS API",
    description="API for JARVIS AI Assistant Web Application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Session middleware (for OAuth tokens)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600,  # 1 hour
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(room.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {
        "message": "JARVIS API is running",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        logger.info("Shutting down application...")
        # Close Supabase client
        await SupabaseService.close_client()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.warning(f"Error during shutdown: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)