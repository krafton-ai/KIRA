"""
Authentication Handler
Web interface authentication method selection and processing
"""

import os
import logging
from typing import Optional, Dict, Any
from enum import Enum

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

from app.cc_web_interface.auth_azure import AzureOAuth
from app.cc_web_interface.auth_slack import SlackOAuth
from app.cc_slack_handlers import is_authorized_user
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class AuthProvider(str, Enum):
    """Supported authentication providers"""
    MICROSOFT = "microsoft"
    SLACK = "slack"
    NONE = "none"  # For development/testing


class AuthHandler:
    """Unified authentication handler"""

    def __init__(self):
        self.provider = self._get_provider()
        logger.info(f"Web interface auth provider: {self.provider}")

        # Initialize OAuth client
        if self.provider == AuthProvider.MICROSOFT:
            self.azure_oauth = AzureOAuth()
        elif self.provider == AuthProvider.SLACK:
            self.slack_oauth = SlackOAuth()

    def _get_provider(self) -> AuthProvider:
        """Get configured authentication provider"""
        settings = get_settings()
        provider = (settings.WEB_INTERFACE_AUTH_PROVIDER or "microsoft").lower()

        logger.info(f"[AUTH_PROVIDER] Read from settings: {provider}")

        try:
            return AuthProvider(provider)
        except ValueError:
            logger.warning(f"Unknown auth provider: {provider}, falling back to microsoft")
            return AuthProvider.MICROSOFT

    def get_redirect_uri(self, request: Request) -> str:
        """Generate OAuth redirect URI"""
        settings = get_settings()

        if settings.WEB_INTERFACE_URL:
            base_url = settings.WEB_INTERFACE_URL
        else:
            base_url = f"{request.url.scheme}://{request.url.netloc}"

        return f"{base_url}/auth/callback"

    async def handle_login(self, request: Request):
        """Start login"""
        if self.provider == AuthProvider.NONE:
            # Development mode - create session immediately
            request.session['user'] = {
                'email': 'dev@localhost',
                'name': 'Developer',
                'id': 'dev_user'
            }
            return RedirectResponse(url="/", status_code=302)

        elif self.provider == AuthProvider.SLACK:
            # Slack OAuth
            redirect_uri = self.get_redirect_uri(request)
            auth_url = self.slack_oauth.get_authorize_url(redirect_uri, state="random_state")
            return RedirectResponse(url=auth_url)

        else:  # MICROSOFT
            # Microsoft OAuth
            redirect_uri = self.get_redirect_uri(request)
            return await self.azure_oauth.client.authorize_redirect(request, redirect_uri)

    async def handle_callback(self, request: Request):
        """Handle OAuth callback"""
        if self.provider == AuthProvider.NONE:
            return RedirectResponse(url="/", status_code=302)

        elif self.provider == AuthProvider.SLACK:
            # Slack OAuth callback
            code = request.query_params.get("code")
            if not code:
                raise HTTPException(status_code=400, detail="No authorization code")

            redirect_uri = self.get_redirect_uri(request)
            token_data = await self.slack_oauth.get_access_token(code, redirect_uri)

            if not token_data:
                raise HTTPException(status_code=400, detail="Failed to get access token")

            # Get OIDC user info
            access_token = token_data.get("access_token")
            if not access_token:
                raise HTTPException(status_code=400, detail="No access token in response")

            user_info = await self.slack_oauth.get_user_info(access_token)

            if not user_info:
                raise HTTPException(status_code=400, detail="Failed to get user info")

            # OIDC userInfo response format: {"ok": true, "sub": "U...", "name": "...", "email": "..."}
            user_name = user_info.get("name", "")
            user_email = user_info.get("email", "")
            user_id = user_info.get("sub", "")  # OIDC uses 'sub' for user ID

            if not is_authorized_user(user_name):
                logger.warning(f"Unauthorized Slack user: {user_name} ({user_email})")
                raise HTTPException(status_code=403, detail=f"Not authorized: {user_name}")

            # Save to session
            request.session['user'] = {
                'email': user_email,
                'name': user_name,
                'id': user_id,
                'provider': 'slack',
                'avatar': user_info.get("picture", "")  # OIDC uses 'picture' for profile image
            }

            return RedirectResponse(url="/", status_code=302)

        else:  # MICROSOFT
            # Microsoft OAuth callback
            token = await self.azure_oauth.client.authorize_access_token(request)
            user_info = await self.azure_oauth.get_user_info_from_token(token)

            if not user_info:
                raise HTTPException(status_code=400, detail="Failed to get user info")

            # Check authorization
            if not is_authorized_user(user_info.get('name', '')):
                logger.warning(f"Unauthorized MS user: {user_info.get('name')} ({user_info.get('email')})")
                raise HTTPException(status_code=403, detail=f"Not authorized: {user_info.get('name')}")

            # Save to session
            request.session['user'] = {
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'id': user_info.get('id'),
                'provider': 'microsoft'
            }

            return RedirectResponse(url="/", status_code=302)

    def get_provider_name(self) -> str:
        """Get current authentication provider name"""
        return self.provider.value


# Singleton instance
auth_handler = AuthHandler()