"""
X (Twitter) OAuth 2.0 PKCE Authentication
X API v2 user authentication
"""

import hashlib
import secrets
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import httpx

from app.config.settings import get_settings

settings = get_settings()

# X OAuth 2.0 endpoints
X_AUTH_URL = "https://twitter.com/i/oauth2/authorize"
X_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
X_REVOKE_URL = "https://api.twitter.com/2/oauth2/revoke"

# OAuth 2.0 Scopes
SCOPES = [
    "tweet.read",
    "tweet.write",
    "users.read",
    "follows.read",
    "follows.write",
    "offline.access",  # Issue Refresh Token
]

# Token storage path
def get_token_cache_dir() -> Path:
    """Return X OAuth token cache directory path"""
    base_dir = settings.FILESYSTEM_BASE_DIR or os.getcwd()
    cache_dir = Path(base_dir) / "data" / "bot_tokens"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def get_token_cache_file() -> Path:
    """Return X OAuth token cache file path"""
    return get_token_cache_dir() / "x_oauth_token.json"


def generate_code_verifier() -> str:
    """Generate PKCE Code Verifier (43-128 character random string)"""
    return secrets.token_urlsafe(64)[:128]


def generate_code_challenge(code_verifier: str) -> str:
    """Generate PKCE Code Challenge (SHA256 hash)"""
    sha256 = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    # Base64 URL-safe encoding (remove padding)
    import base64
    return base64.urlsafe_b64encode(sha256).decode('utf-8').rstrip('=')


def get_authorization_url(redirect_uri: str, state: str, code_challenge: str) -> str:
    """
    Generate X OAuth 2.0 authorization URL

    Args:
        redirect_uri: Callback URL
        state: CSRF prevention token
        code_challenge: PKCE code challenge

    Returns:
        Authorization URL
    """
    params = {
        "response_type": "code",
        "client_id": settings.X_OAUTH2_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    # Generate URL
    from urllib.parse import urlencode
    return f"{X_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_token(
    code: str,
    code_verifier: str,
    redirect_uri: str
) -> Optional[Dict[str, Any]]:
    """
    Exchange Authorization Code for Access Token

    Args:
        code: Authorization code
        code_verifier: PKCE code verifier
        redirect_uri: Callback URL

    Returns:
        Token info (access_token, refresh_token, expires_in, etc.)
    """
    try:
        # Basic Authentication (Client ID:Client Secret)
        import base64
        credentials = f"{settings.X_OAUTH2_CLIENT_ID}:{settings.X_OAUTH2_CLIENT_SECRET}"
        b64_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

        headers = {
            "Authorization": f"Basic {b64_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(X_TOKEN_URL, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()

        logging.info(f"[X_OAUTH] Token exchanged successfully")
        return token_data

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        logging.error(f"[X_OAUTH] Token exchange failed (HTTP {e.response.status_code}): {error_detail}")
        return None
    except Exception as e:
        logging.error(f"[X_OAUTH] Token exchange error: {e}")
        return None


async def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """
    Issue new Access Token using Refresh Token

    Args:
        refresh_token: Refresh token

    Returns:
        New token info
    """
    try:
        import base64
        credentials = f"{settings.X_OAUTH2_CLIENT_ID}:{settings.X_OAUTH2_CLIENT_SECRET}"
        b64_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

        headers = {
            "Authorization": f"Basic {b64_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(X_TOKEN_URL, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()

        logging.info(f"[X_OAUTH] Token refreshed successfully")
        return token_data

    except Exception as e:
        logging.error(f"[X_OAUTH] Token refresh error: {e}")
        return None


def save_token(token_data: Dict[str, Any]) -> None:
    """
    Save token to file

    Args:
        token_data: Token info
    """
    try:
        token_cache_file = get_token_cache_file()

        # Calculate expiration time
        expires_in = token_data.get("expires_in", 7200)  # Default 2 hours
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        cache_data = {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "token_type": token_data.get("token_type", "bearer"),
            "scope": token_data.get("scope", " ".join(SCOPES)),
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        # Save as JSON file
        with open(token_cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)

        logging.info(f"[X_OAUTH] Token saved to {token_cache_file}")

    except Exception as e:
        logging.error(f"[X_OAUTH] Failed to save token: {e}")


def load_token() -> Optional[Dict[str, Any]]:
    """
    Load saved token

    Returns:
        Token info (None if not found)
    """
    try:
        token_cache_file = get_token_cache_file()

        if not token_cache_file.exists():
            return None

        with open(token_cache_file, 'r', encoding='utf-8') as f:
            token_data = json.load(f)

        # Check expiration time (return token data even if expired - refresh token may still be valid)
        expires_at_str = token_data.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() >= expires_at:
                logging.warning(f"[X_OAUTH] Access token expired at {expires_at}, but returning for potential refresh")

        return token_data

    except Exception as e:
        logging.error(f"[X_OAUTH] Failed to load token: {e}")
        return None


async def get_valid_access_token() -> Optional[str]:
    """
    Get valid Access Token (auto-refresh if needed)

    Returns:
        Access Token (None if not available)
    """
    token_data = load_token()

    if not token_data:
        logging.warning("[X_OAUTH] No cached token found")
        return None

    # Check token expiration time
    expires_at_str = token_data.get("expires_at")
    if expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str)
        time_remaining = expires_at - datetime.now()

        # Token already expired or will expire soon (within 10 minutes)
        if time_remaining.total_seconds() < 600:
            if time_remaining.total_seconds() < 0:
                logging.info("[X_OAUTH] Token already expired, refreshing...")
            else:
                logging.info("[X_OAUTH] Token expiring soon, refreshing...")

            refresh_token = token_data.get("refresh_token")

            if refresh_token:
                new_token_data = await refresh_access_token(refresh_token)
                if new_token_data:
                    save_token(new_token_data)
                    return new_token_data.get("access_token")
                else:
                    logging.error("[X_OAUTH] Failed to refresh token")
                    return None
            else:
                logging.error("[X_OAUTH] No refresh token available")
                return None

    return token_data.get("access_token")


def delete_token() -> None:
    """Delete saved token"""
    try:
        token_cache_file = get_token_cache_file()
        if token_cache_file.exists():
            token_cache_file.unlink()
            logging.info("[X_OAUTH] Token deleted")
    except Exception as e:
        logging.error(f"[X_OAUTH] Failed to delete token: {e}")
