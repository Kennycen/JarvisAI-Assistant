from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os
import json
import logging
from server.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

SCOPES = ['https://www.googleapis.com/auth/calendar']

@router.get("/google")
async def google_auth(request: Request):
    """Initiate Google OAuth flow"""
    try:
        # Allow HTTP for localhost development
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
        flow = Flow.from_client_secrets_file(
            "credentials.json",
            scopes=SCOPES,
            redirect_uri=settings.OAUTH_REDIRECT_URI
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store state in session
        request.session['oauth_state'] = state
        
        return RedirectResponse(url=authorization_url)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500, 
            detail="credentials.json not found. Please download from Google Cloud Console."
        )
    except Exception as e:
        logger.error(f"OAuth initiation error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth error: {str(e)}")

@router.get("/callback")
async def oauth_callback(request: Request, code: str = None, state: str = None):
    """Handle OAuth callback"""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    # Verify state
    stored_state = request.session.get('oauth_state')
    if not stored_state or state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        # Allow HTTP for localhost development
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
        flow = Flow.from_client_secrets_file(
            "credentials.json",
            scopes=SCOPES,
            redirect_uri=settings.OAUTH_REDIRECT_URI,
            state=state
        )
        
        # Get the full URL with query parameters
        full_url = str(request.url)
        flow.fetch_token(authorization_response=full_url)
        credentials = flow.credentials
        
        # Store credentials in session as JSON string
        request.session['google_credentials'] = credentials.to_json()
        
        # Clear the state after successful auth
        request.session.pop('oauth_state', None)
        
        # Redirect to frontend
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?auth=success")
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/status")
async def auth_status(request: Request):
    """Check authentication status"""
    credentials_json = request.session.get('google_credentials')
    
    if not credentials_json:
        return JSONResponse({"authenticated": False})
    
    try:
        # Parse JSON string safely
        if isinstance(credentials_json, str):
            credentials_dict = json.loads(credentials_json)
        else:
            credentials_dict = credentials_json
            
        credentials = Credentials.from_authorized_user_info(credentials_dict, SCOPES)
        
        # Try to get email from token info
        email = None
        try:
            # Refresh token to get user info if needed
            if credentials.expired and credentials.refresh_token:
                from google.auth.transport.requests import Request as GoogleRequest
                credentials.refresh(GoogleRequest())
            
            # Get email from token info (if available)
            if hasattr(credentials, 'id_token') and credentials.id_token:
                email = credentials.id_token.get('email')
        except:
            pass  # Email not available, that's okay
        
        return JSONResponse({
            "authenticated": True,
            "email": email
        })
    except Exception as e:
        logger.error(f"Error parsing credentials: {e}")
        return JSONResponse({"authenticated": False})

@router.post("/logout")
async def logout(request: Request):
    """Logout and clear session"""
    request.session.clear()
    return JSONResponse({"status": "logged_out"})