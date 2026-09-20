from __future__ import annotations

import html
import json
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from jarvis.config import Settings, get_settings
from jarvis.core.connectors import (
    DEFAULT_USER_ID,
    ConnectorSpec,
    ConnectorState,
    MetaStore,
    get_connector,
    read_all,
    read_state,
)
from jarvis.core.errors import JarvisError
from jarvis.core.google import oauth
from jarvis.core.google.auth import FileTokenStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connectors", tags=["connectors"])

# An authorization that isn't finished in this long is abandoned.
_STATE_TTL_SECONDS = 600
# state -> (connector_id, expires_at, code_verifier). In-process is fine for a
# single-user app; a restart mid-authorization just means clicking Connect again.
# The verifier is PKCE: Google will not swap the code without the same secret
# that was used to build the consent URL.
_PENDING: dict[str, tuple[str, float, str]] = {}


def _remember_state(state: str, connector_id: str, code_verifier: str) -> None:
    now = time.monotonic()
    for key, (_, expires, _) in list(_PENDING.items()):
        if expires <= now:
            del _PENDING[key]
    _PENDING[state] = (connector_id, now + _STATE_TTL_SECONDS, code_verifier)


def _claim_state(state: str | None, connector_id: str) -> str | None:
    if not state:
        return None
    pending = _PENDING.pop(state, None)
    if pending is None:
        return None
    remembered_id, expires, verifier = pending
    if remembered_id != connector_id or expires <= time.monotonic():
        return None
    return verifier


class ConnectorView(BaseModel):
    id: str
    name: str
    description: str
    category: str
    provider: str
    available: bool
    status: str
    account: str | None = None
    connected_at: str | None = None


class AuthorizationView(BaseModel):
    authorization_url: str


def _view(state: ConnectorState) -> ConnectorView:
    return ConnectorView(
        id=state.spec.id,
        name=state.spec.name,
        description=state.spec.description,
        category=state.spec.category,
        provider=state.spec.provider,
        available=state.spec.available,
        status=state.status,
        account=state.account,
        connected_at=state.connected_at,
    )


def _require(connector_id: str) -> ConnectorSpec:
    spec = get_connector(connector_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {connector_id}")
    return spec


def _require_connectable(connector_id: str) -> ConnectorSpec:
    spec = _require(connector_id)
    if not spec.available:
        raise HTTPException(status_code=400, detail=f"{spec.name} is not available yet")
    if spec.provider != "google":
        raise HTTPException(status_code=400, detail=f"No OAuth support for {spec.provider}")
    return spec


@router.get("", response_model=list[ConnectorView])
def list_connectors(
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[ConnectorView]:
    return [_view(state) for state in read_all(DEFAULT_USER_ID, settings.token_dir)]


@router.post("/{connector_id}/connect", response_model=AuthorizationView)
def connect(
    connector_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthorizationView:
    """Hand the frontend a URL to open in a popup. Nothing is stored yet."""
    spec = _require_connectable(connector_id)
    try:
        flow = oauth.build_flow(spec, settings)
        url, state = oauth.authorization_url(flow)
    except JarvisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not flow.code_verifier:
        raise HTTPException(status_code=500, detail="OAuth flow did not produce a PKCE verifier")
    _remember_state(state, spec.id, flow.code_verifier)
    return AuthorizationView(authorization_url=url)


def _popup_result(settings: Settings, connector_id: str, error: str | None) -> HTMLResponse:
    """A page whose only job is to tell the opener what happened and vanish."""
    payload = json.dumps(
        {"source": "jarvis-oauth", "connectorId": connector_id, "ok": error is None,
         "error": error}
    )
    target = json.dumps(settings.frontend_origin)
    message = "Connected. You can close this window." if error is None else error
    body = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Jarvis</title>
<style>
  body {{ background:#101114; color:#e9eef3; font-family:ui-monospace,monospace;
          display:flex; align-items:center; justify-content:center; height:100vh;
          margin:0; text-align:center; padding:1rem; }}
</style></head>
<body><p>{html.escape(message)}</p>
<script>
  try {{ window.opener && window.opener.postMessage({payload}, {target}); }} catch (e) {{}}
  setTimeout(function () {{ window.close(); }}, 400);
</script></body></html>"""
    return HTMLResponse(body)


@router.get("/{connector_id}/callback", response_class=HTMLResponse)
def callback(
    connector_id: str,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> HTMLResponse:
    spec = _require_connectable(connector_id)

    state = request.query_params.get("state")
    verifier = _claim_state(state, spec.id)
    if not verifier:
        return _popup_result(settings, connector_id, "Authorization expired. Try again.")

    if denial := request.query_params.get("error"):
        return _popup_result(settings, connector_id, f"Google refused: {denial}")

    try:
        flow = oauth.build_flow(spec, settings, state=state)
        flow.code_verifier = verifier
        # Rebuilt rather than taken from request.url so it matches the registered
        # redirect URI byte for byte even behind a proxy.
        response_url = f"{oauth.redirect_uri(spec, settings)}?{request.url.query}"
        credentials = oauth.exchange_code(flow, response_url)
    except Exception as exc:
        logger.exception("Token exchange failed for %s", spec.id)
        return _popup_result(settings, connector_id, f"Token exchange failed: {exc}")

    FileTokenStore(settings.token_dir, spec.id).save(DEFAULT_USER_ID, credentials)
    MetaStore(settings.token_dir).save(
        DEFAULT_USER_ID, spec.id, oauth.fetch_account(spec, credentials)
    )
    logger.info("Connected %s", spec.id)
    return _popup_result(settings, connector_id, None)


@router.delete("/{connector_id}", response_model=ConnectorView)
def disconnect(
    connector_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ConnectorView:
    spec = _require(connector_id)
    store = FileTokenStore(settings.token_dir, spec.id)

    try:
        if credentials := store.load(DEFAULT_USER_ID):
            oauth.revoke(credentials)
    except Exception:
        logger.warning("Could not load %s for revocation; deleting anyway", spec.id)

    store.delete(DEFAULT_USER_ID)
    MetaStore(settings.token_dir).delete(DEFAULT_USER_ID, spec.id)
    logger.info("Disconnected %s", spec.id)

    return _view(read_state(spec, DEFAULT_USER_ID, settings.token_dir))
