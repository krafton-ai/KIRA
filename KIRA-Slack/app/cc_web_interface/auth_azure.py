"""
Azure/Microsoft OAuth Authentication
User authentication via Microsoft Azure AD
"""

import logging
from typing import Optional, Dict, Any

from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

from app.config.settings import get_settings


class AzureOAuth:
    """Azure/Microsoft OAuth 2.0 authentication handler"""

    def __init__(self):
        settings = get_settings()

        # OAuth configuration
        config = Config(environ={
            "MS_CLIENT_ID": settings.WEB_MS365_CLIENT_ID,
            "MS_CLIENT_SECRET": settings.WEB_MS365_CLIENT_SECRET or "",
            "MS_TENANT_ID": settings.WEB_MS365_TENANT_ID,
        })

        self.oauth = OAuth(config)

        # Register Microsoft OAuth
        self.oauth.register(
            name='microsoft',
            client_id=config.get('MS_CLIENT_ID'),
            client_secret=config.get('MS_CLIENT_SECRET'),
            server_metadata_url=f'https://login.microsoftonline.com/{config.get("MS_TENANT_ID")}/v2.0/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile User.Read',
            },
        )

        self.client = self.oauth.microsoft

    async def get_user_info_from_token(self, token: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extract user info from OAuth token

        Args:
            token: OAuth token

        Returns:
            User info (email, name, etc.)
        """
        try:
            # Get user info via Microsoft Graph API
            resp = await self.client.get(
                'https://graph.microsoft.com/v1.0/me',
                token=token
            )
            user_data = resp.json()

            return {
                'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                'name': user_data.get('displayName'),
                'id': user_data.get('id'),
            }
        except Exception as e:
            logging.error(f"[AZURE_AUTH] Error getting user info: {e}")
            return None
