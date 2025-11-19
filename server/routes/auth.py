from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
import os
import logging
from typing import Dict, Any
from server.config import settings
from server.middleware.auth import get_current_user
from server.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar',
]


def build_google_client_config(redirect_uri: str, state: str | None = None) -> Dict[str, Any]:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth client env vars missing")

    config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": [redirect_uri],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        state=state,
    )
    return flow


@router.get("/google/calendar")
async def google_calendar_auth(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Initiate Google Calendar OAuth flow for authenticated user"""
    try:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        redirect_uri = "http://localhost:8000/api/auth/google/calendar/callback"

        flow = build_google_client_config(redirect_uri)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        client = SupabaseService.get_client()
        client.table("oauth_states").insert({
            "state": state,
            "user_id": current_user['user_id']
        }).execute()

        logger.info(f"Stored OAuth state {state} for user {current_user['user_id']}")

        return JSONResponse({"authorization_url": authorization_url})
    except Exception as e:
        logger.error(f"OAuth initiation error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth error: {str(e)}")


@router.get("/google/calendar/callback")
async def google_calendar_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None
):
    """Handle Google Calendar OAuth callback"""
    if not code:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}?calendar_auth=error&message=no_code"
        )

    if not state:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}?calendar_auth=error&message=no_state"
        )

    try:
        client = SupabaseService.get_client()
        state_response = client.table("oauth_states").select("*").eq("state", state).execute()

        if not state_response.data:
            logger.error(f"State {state} not found in database")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}?calendar_auth=error&message=invalid_state"
            )

        state_data = state_response.data[0]
        user_id = state_data['user_id']

        client.table("oauth_states").delete().eq("state", state).execute()

        logger.info(f"Verified OAuth state {state} for user {user_id}")

    except Exception as e:
        logger.error(f"Error verifying state: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}?calendar_auth=error&message=state_verification_failed"
        )

    try:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        redirect_uri = "http://localhost:8000/api/auth/google/calendar/callback"

        flow = build_google_client_config(redirect_uri, state=state)

        full_url = str(request.url)
        flow.fetch_token(authorization_response=full_url)
        credentials = flow.credentials

        credentials_json = credentials.to_json()
        success = await SupabaseService.save_calendar_credentials(
            user_id,
            credentials_json
        )

        if not success:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}?calendar_auth=error&message=save_failed"
            )

        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}?calendar_auth=success"
        )

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}?calendar_auth=error&message={str(e)}"
        )


@router.get("/calendar/status")
async def calendar_status(current_user: dict = Depends(get_current_user)):
    """Check if user has calendar credentials"""
    try:
        credentials = await SupabaseService.get_calendar_credentials(
            current_user['user_id']
        )

        if credentials:
            return JSONResponse({
                "authenticated": True,
                "email": current_user.get('email')
            })
        else:
            return JSONResponse({"authenticated": False})
    except Exception as e:
        logger.error(f"Error checking calendar status: {e}")
        return JSONResponse({"authenticated": False})


@router.post("/calendar/disconnect")
async def disconnect_calendar(current_user: dict = Depends(get_current_user)):
    """Disconnect calendar credentials"""
    try:
        client = SupabaseService.get_client()
        client.table("calendar_credentials").delete().eq(
            "user_id", current_user['user_id']
        ).execute()

        return JSONResponse({"status": "disconnected"})
    except Exception as e:
        logger.error(f"Error disconnecting calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))