"""
Authentication Routes
User authentication routes (/auth/login, /auth/callback, /auth/logout)
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from app.cc_web_interface.auth_handler import auth_handler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    """Start login"""
    return await auth_handler.handle_login(request)


@router.get("/callback")
async def auth_callback(request: Request):
    """Handle OAuth callback"""
    return await auth_handler.handle_callback(request)


@router.get("/logout")
async def logout(request: Request):
    """Logout"""
    provider = request.session.get('user', {}).get('provider', 'unknown')
    request.session.clear()

    return HTMLResponse(
        content=f"""
        <h1>Logout Complete</h1>
        <p>You have been logged out from your {provider.title()} account.</p>
        <p><a href="/">Log in again</a></p>
        """,
        status_code=200
    )


@router.get("/status")
async def auth_status(request: Request):
    """Current authentication status"""
    user = request.session.get('user')

    if not user:
        return {
            "logged_in": False,
            "user": None
        }

    return {
        "logged_in": True,
        "user": {
            "name": user.get('name', ''),
            "email": user.get('email', ''),
            "id": user.get('id', ''),
            "provider": user.get('provider', 'unknown')
        }
    }