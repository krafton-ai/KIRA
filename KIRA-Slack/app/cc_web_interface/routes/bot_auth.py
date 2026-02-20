"""
Bot Authentication Routes
Authentication setup routes for bot to use external APIs
(X/Twitter, etc.)
"""

import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.cc_slack_handlers import is_authorized_user
from app.cc_utils import x_helper
from app.cc_web_interface.oauth_session_store import oauth_session_store
from app.cc_web_interface.utils import get_redirect_uri

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bot/auth", tags=["bot-auth"])


def require_admin(request: Request) -> dict:
    """Check admin permissions"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not is_authorized_user(user.get("name", "")):
        raise HTTPException(status_code=403, detail="Not authorized")

    return user


# ========== X(Twitter) OAuth 2.0 ==========

@router.get("/x/start")
async def x_auth_start(request: Request):
    """Start X OAuth 2.0 authentication (no login required - for initial setup)"""
    try:
        # Generate PKCE
        code_verifier = x_helper.generate_code_verifier()
        code_challenge = x_helper.generate_code_challenge(code_verifier)

        # State (CSRF prevention)
        state = x_helper.secrets.token_urlsafe(32)

        # Store in file-based session
        oauth_session_store.store(state, {
            "code_verifier": code_verifier,
        })

        # Redirect URI
        redirect_uri = get_redirect_uri(request, 'x_auth_callback')

        # Generate X authorization URL
        auth_url = x_helper.get_authorization_url(redirect_uri, state, code_challenge)

        logger.info(f"[X_AUTH] Starting OAuth flow, state={state}")

        return RedirectResponse(url=auth_url)

    except Exception as e:
        logger.error(f"[X_AUTH] Start error: {e}")
        return HTMLResponse(
            content=f"<h1>X Authentication Start Failed</h1><p>{str(e)}</p>",
            status_code=500
        )


@router.get("/x/callback")
async def x_auth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """X OAuth 2.0 Callback"""
    try:
        # Error handling
        if error:
            logger.error(f"[X_AUTH] OAuth error: {error} - {error_description}")
            return HTMLResponse(
                content=f"""
                <html>
                <head><title>X Authentication Failed</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>X (Twitter) Authentication Failed</h1>
                    <p><strong>Error:</strong> {error}</p>
                    <p><strong>Description:</strong> {error_description or 'N/A'}</p>
                    <p><a href="/bot/auth/x/start">Try again</a></p>
                </body>
                </html>
                """,
                status_code=400
            )

        # Validate parameters
        if not code or not state:
            logger.error("[X_AUTH] Missing code or state")
            return HTMLResponse(
                content="<h1>Invalid Request</h1><p>Required parameters are missing.</p>",
                status_code=400
            )

        # Get session data
        session_data = oauth_session_store.retrieve(state)
        if not session_data:
            logger.error(f"[X_AUTH] Invalid state: {state}")
            return HTMLResponse(
                content="<h1>Invalid Request</h1><p>Session has expired or request is invalid.</p>",
                status_code=400
            )

        code_verifier = session_data["code_verifier"]
        user_name = session_data.get("user_name", "Unknown")

        # Delete session (one-time use)
        oauth_session_store.delete(state)

        # Redirect URI
        redirect_uri = get_redirect_uri(request, 'x_auth_callback')

        # Exchange Authorization Code for Access Token
        token_data = await x_helper.exchange_code_for_token(code, code_verifier, redirect_uri)

        if not token_data:
            return HTMLResponse(
                content="<h1>Token Issuance Failed</h1><p>Failed to receive token from X API.</p>",
                status_code=500
            )

        # Save token
        x_helper.save_token(token_data)

        logger.info(f"[X_AUTH] OAuth completed for {user_name}")

        return HTMLResponse(
            content="<body style='background:#000;color:#fff;font-family:monospace;padding:20px'>X OAuth authentication completed. You can close this window.</body>",
            status_code=200
        )

    except Exception as e:
        logger.error(f"[X_AUTH] Callback error: {e}")
        return HTMLResponse(
            content=f"<h1>X Authentication Failed</h1><p>{str(e)}</p>",
            status_code=500
        )


@router.get("/x/status")
async def x_auth_status():
    """Check X OAuth authentication status (no login required)"""
    try:
        token_data = x_helper.load_token()

        if not token_data:
            return {
                "authenticated": False,
                "message": "X authentication is required."
            }

        # Check expiration time
        expires_at_str = token_data.get("expires_at")
        from datetime import datetime
        expires_at = datetime.fromisoformat(expires_at_str)
        time_remaining = expires_at - datetime.now()

        if time_remaining.total_seconds() <= 0:
            return {
                "authenticated": False,
                "message": "Token has expired. Re-authentication is required."
            }

        return {
            "authenticated": True,
            "scope": token_data.get("scope", ""),
            "expires_at": expires_at_str,
            "time_remaining_seconds": int(time_remaining.total_seconds()),
            "time_remaining_human": str(time_remaining).split('.')[0],
            "created_at": token_data.get("created_at"),
        }

    except Exception as e:
        logger.error(f"[X_AUTH] Status check error: {e}")
        return {
            "authenticated": False,
            "error": str(e)
        }


@router.post("/x/logout")
async def x_auth_logout():
    """Delete X OAuth token (no login required)"""
    try:
        x_helper.delete_token()
        logger.info("[X_AUTH] Token deleted")
        return {
            "success": True,
            "message": "X authentication token has been deleted."
        }
    except Exception as e:
        logger.error(f"[X_AUTH] Logout error: {e}")
        return {
            "success": False,
            "error": str(e)
        }