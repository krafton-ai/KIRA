"""
OAuth Session Store
File-based storage for temporary data during OAuth flow
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class OAuthSessionStore:
    """
    Store OAuth session data in file system
    Allows OAuth flow to continue even after server restart
    """

    def __init__(self, store_path: Optional[Path] = None):
        """
        Args:
            store_path: Path to store session data
        """
        if store_path is None:
            settings = get_settings()
            base_dir = settings.FILESYSTEM_BASE_DIR or os.getcwd()
            store_path = Path(base_dir) / "data" / "oauth_sessions"

        self.store_path = store_path
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.session_file = self.store_path / "sessions.json"

        # Initialize and cleanup expired sessions
        self._load_sessions()
        self._cleanup_expired()

    def _load_sessions(self) -> Dict[str, Any]:
        """Load session data"""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load OAuth sessions: {e}")
                return {}
        return {}

    def _save_sessions(self, sessions: Dict[str, Any]):
        """Save session data"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump(sessions, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save OAuth sessions: {e}")

    def _cleanup_expired(self):
        """Clean up expired sessions (older than 24 hours)"""
        sessions = self._load_sessions()
        now = datetime.now()
        cleaned = {}

        for state, data in sessions.items():
            try:
                created_at = datetime.fromisoformat(data.get("created_at"))
                if now - created_at < timedelta(hours=24):
                    cleaned[state] = data
                else:
                    logger.info(f"Cleaned expired OAuth session: {state}")
            except Exception as e:
                logger.error(f"Error processing session {state}: {e}")

        if len(cleaned) < len(sessions):
            self._save_sessions(cleaned)

    def store(self, state: str, data: Dict[str, Any]) -> bool:
        """
        Store OAuth session data

        Args:
            state: OAuth state parameter
            data: Data to store (code_verifier, etc.)

        Returns:
            Whether storage was successful
        """
        try:
            sessions = self._load_sessions()
            sessions[state] = {
                **data,
                "created_at": datetime.now().isoformat()
            }
            self._save_sessions(sessions)
            logger.info(f"Stored OAuth session: {state}")
            return True
        except Exception as e:
            logger.error(f"Failed to store OAuth session: {e}")
            return False

    def retrieve(self, state: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve OAuth session data

        Args:
            state: OAuth state parameter

        Returns:
            Session data or None
        """
        sessions = self._load_sessions()
        data = sessions.get(state)

        if data:
            logger.info(f"Retrieved OAuth session: {state}")
        else:
            logger.warning(f"OAuth session not found: {state}")

        return data

    def delete(self, state: str) -> bool:
        """
        Delete OAuth session data

        Args:
            state: OAuth state parameter

        Returns:
            Whether deletion was successful
        """
        try:
            sessions = self._load_sessions()
            if state in sessions:
                del sessions[state]
                self._save_sessions(sessions)
                logger.info(f"Deleted OAuth session: {state}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete OAuth session: {e}")
            return False

    def clear_all(self) -> bool:
        """
        Delete all session data

        Returns:
            Whether deletion was successful
        """
        try:
            self._save_sessions({})
            logger.info("Cleared all OAuth sessions")
            return True
        except Exception as e:
            logger.error(f"Failed to clear OAuth sessions: {e}")
            return False


# Singleton instance
oauth_session_store = OAuthSessionStore()