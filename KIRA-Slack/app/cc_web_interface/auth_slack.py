"""
Slack OpenID Connect (OIDC) Authentication for Web Interface
Slack login for web interface access (OpenID Connect)
"""

import os
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class SlackOAuth:
    """Slack OpenID Connect authentication handler"""

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.WEB_SLACK_CLIENT_ID or ""
        self.client_secret = settings.WEB_SLACK_CLIENT_SECRET or ""
        self.team_id = settings.SLACK_TEAM_ID or ""

        # OpenID Connect endpoints
        self.authorize_url = "https://slack.com/openid/connect/authorize"
        self.token_url = "https://slack.com/api/openid.connect.token"
        self.user_info_url = "https://slack.com/api/openid.connect.userInfo"

    def get_authorize_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Slack OIDC authorization URL"""
        params = {
            "client_id": self.client_id,
            "scope": "openid email profile",  # OpenID Connect scopes
            "redirect_uri": redirect_uri,
            "response_type": "code",  # OIDC requires this
        }

        if self.team_id:
            params["team"] = self.team_id

        if state:
            params["state"] = state

        url = f"{self.authorize_url}?{urlencode(params)}"
        logger.info(f"[SLACK_OIDC] Generated authorize URL: {url}")
        logger.info(f"[SLACK_OIDC] Client ID: {self.client_id}")
        logger.info(f"[SLACK_OIDC] Redirect URI: {redirect_uri}")
        logger.info(f"[SLACK_OIDC] Scopes: openid email profile")
        return url

    async def get_access_token(self, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token (OIDC)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"  # OIDC requires this
                }
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"[SLACK_OIDC] Token response: {data}")
                if data.get("ok"):
                    return data
                else:
                    logger.error(f"Slack OIDC error: {data.get('error')}")
                    return None
            else:
                logger.error(f"Slack OIDC token exchange failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None

    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get Slack user info (OIDC userInfo)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"[SLACK_OIDC] User info response: {data}")
                if data.get("ok"):
                    # OIDC userInfo returns user data directly
                    return data
                else:
                    logger.error(f"Slack OIDC user info error: {data.get('error')}")
                    return None
            else:
                logger.error(f"Failed to get Slack OIDC user info: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None


# Singleton instance
slack_oauth = SlackOAuth()