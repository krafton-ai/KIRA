"""
Web Interface Utilities
Common helper functions
"""

import logging
from typing import Optional

from fastapi import Request

logger = logging.getLogger(__name__)


def get_redirect_uri(request: Request, endpoint: str) -> str:
    """
    Generate OAuth redirect URI
    Uses WEB_INTERFACE_URL if set, otherwise generates from current request

    Args:
        request: FastAPI Request object
        endpoint: Endpoint name

    Returns:
        Complete redirect URI
    """
    from app.config.settings import get_settings
    settings = get_settings()

    if settings.WEB_INTERFACE_URL:
        # Use URL specified by environment variable
        return f"{settings.WEB_INTERFACE_URL}{request.url_for(endpoint).path}"
    else:
        # Generate URL from current request
        return str(request.url_for(endpoint))


async def get_slack_user_id(email: str, slack_client) -> Optional[str]:
    """
    Find Slack user ID by email

    Args:
        email: User email
        slack_client: Slack API client

    Returns:
        Slack User ID or None
    """
    try:
        response = await slack_client.users_lookupByEmail(email=email)
        if response.get('ok'):
            user = response.get('user', {})
            return user.get('id')
        else:
            logger.error(f"Failed to find Slack user by email {email}: {response.get('error')}")
            return None
    except Exception as e:
        logger.error(f"Error looking up Slack user: {e}")
        return None


def is_development_mode() -> bool:
    """
    Check if in development mode
    Returns True if WEB_INTERFACE_AUTH_PROVIDER is 'none'

    Returns:
        Whether in development mode
    """
    from app.config.settings import get_settings
    settings = get_settings()
    return (settings.WEB_INTERFACE_AUTH_PROVIDER or "").lower() == "none"


def get_session_user(request: Request) -> Optional[dict]:
    """
    Get user info from session

    Args:
        request: FastAPI Request object

    Returns:
        User info dictionary or None
    """
    return request.session.get('user')


def require_auth(request: Request) -> bool:
    """
    Check if authentication is required

    Args:
        request: FastAPI Request object

    Returns:
        Whether authentication is required
    """
    # No authentication needed in development mode
    if is_development_mode():
        return False

    # Check if user info exists in session
    user = get_session_user(request)
    return user is None