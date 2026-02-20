"""
Confirm SQLite Database Manager
SQLite database for managing user confirmation requests
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config.settings import get_settings


def get_db_path() -> Path:
    """Return SQLite database file path"""
    settings = get_settings()
    base_dir = settings.FILESYSTEM_BASE_DIR or os.getcwd()
    db_dir = Path(base_dir) / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "confirms.db"


def get_connection() -> sqlite3.Connection:
    """Return SQLite connection (with Row factory set)"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database and create tables"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS confirms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            confirm_id TEXT NOT NULL UNIQUE,
            channel_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            user_name TEXT,
            confirm_message TEXT NOT NULL,
            original_request_text TEXT NOT NULL,
            thread_ts TEXT,
            confirmed INTEGER DEFAULT 0,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_confirm_id
        ON confirms(confirm_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_channel_user_pending
        ON confirms(channel_id, user_id, confirmed)
    """)

    conn.commit()
    conn.close()


def cancel_user_pending_confirms(user_id: str, channel_id: str, thread_ts: str = None) -> int:
    """
    Change pending confirms for a specific user in a channel/thread to expired status
    Used to cancel previous proposals when a new proposal is sent

    Args:
        user_id: User ID
        channel_id: Channel ID
        thread_ts: Thread timestamp (None for main channel only)

    Returns:
        Number of cancelled confirms
    """
    conn = get_connection()
    cursor = conn.cursor()

    updated_at = datetime.now().isoformat()

    if thread_ts:
        # Cancel pending only in specific thread
        cursor.execute("""
            UPDATE confirms
            SET confirmed = -2,
                status = 'expired',
                updated_at = ?
            WHERE user_id = ? AND channel_id = ? AND thread_ts = ? AND confirmed = 0
        """, (updated_at, user_id, channel_id, thread_ts))
    else:
        # Cancel pending only in main channel (thread_ts=NULL)
        cursor.execute("""
            UPDATE confirms
            SET confirmed = -2,
                status = 'expired',
                updated_at = ?
            WHERE user_id = ? AND channel_id = ? AND thread_ts IS NULL AND confirmed = 0
        """, (updated_at, user_id, channel_id))

    conn.commit()
    cancelled_count = cursor.rowcount
    conn.close()

    return cancelled_count


def add_confirm_request(
    confirm_id: str,
    channel_id: str,
    user_id: str,
    user_name: str,
    confirm_message: str,
    original_request_text: str,
    thread_ts: str = None
) -> bool:
    """
    Add new confirm request
    Automatically cancels previous pending confirms for this user in the channel before adding

    Args:
        confirm_id: Unique confirm ID
        channel_id: Channel ID
        user_id: User ID who needs to confirm
        user_name: User name
        confirm_message: Confirmation message ("Would you like me to help you with this?")
        original_request_text: Original request text
        thread_ts: Thread timestamp (optional, for thread isolation)

    Returns:
        Whether addition was successful
    """
    import logging

    # First cancel previous pending confirms for this user in the channel/thread
    cancelled = cancel_user_pending_confirms(user_id, channel_id, thread_ts)
    if cancelled > 0:
        logging.info(f"[CONFIRM_DB] Cancelled {cancelled} previous pending confirms for user {user_id} in channel {channel_id} (thread_ts={thread_ts})")

    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().isoformat()

    try:
        cursor.execute("""
            INSERT INTO confirms (
                confirm_id, channel_id, user_id, user_name, confirm_message,
                original_request_text, thread_ts, confirmed, response, created_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, 'pending')
        """, (confirm_id, channel_id, user_id, user_name, confirm_message,
              original_request_text, thread_ts, created_at))

        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Duplicate confirm_id
        success = False
    finally:
        conn.close()

    return success


def update_confirm_response(
    confirm_id: str,
    user_id: str,
    approved: bool,
    response: str
) -> bool:
    """
    Update confirm response

    Args:
        confirm_id: Confirm ID
        user_id: User ID
        approved: Whether approved (True: approved, False: rejected)
        response: User's actual response text

    Returns:
        Whether update was successful
    """
    conn = get_connection()
    cursor = conn.cursor()

    updated_at = datetime.now().isoformat()
    confirmed = 1 if approved else -1
    status = 'approved' if approved else 'rejected'

    cursor.execute("""
        UPDATE confirms
        SET confirmed = ?,
            response = ?,
            updated_at = ?,
            status = ?
        WHERE confirm_id = ? AND user_id = ?
    """, (confirmed, response, updated_at, status, confirm_id, user_id))

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()

    return success


def get_confirm_by_id(confirm_id: str) -> Optional[Dict[str, Any]]:
    """
    Get specific confirm

    Args:
        confirm_id: Confirm ID

    Returns:
        Confirm info or None
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, confirm_id, channel_id, user_id, user_name, confirm_message,
            original_request_text, thread_ts, confirmed, response, created_at, updated_at, status
        FROM confirms
        WHERE confirm_id = ?
    """, (confirm_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_channel_pending_confirms(channel_id: str, user_id: str, thread_ts: str = None) -> List[Dict[str, Any]]:
    """
    Get pending confirms for a specific user in a channel (within last 24 hours)
    Thread isolation via thread_ts:
    - Dynamic suggester confirm (thread_ts=NULL): Can respond from anywhere
    - Proactive suggester confirm (thread_ts=value): Can only respond in that thread

    Args:
        channel_id: Channel ID
        user_id: User ID
        thread_ts: Thread timestamp (None for main channel only, value for specific thread or NULL confirm)

    Returns:
        List of pending confirms (within last 24 hours)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, confirm_id, channel_id, user_id, user_name, confirm_message,
            original_request_text, thread_ts, confirmed, response, created_at, updated_at, status
        FROM confirms
        WHERE channel_id = ? AND user_id = ? AND confirmed = 0
          AND created_at >= datetime('now', '-12 hours')
          AND (thread_ts = ? OR thread_ts IS NULL)
        ORDER BY created_at DESC
    """, (channel_id, user_id, thread_ts))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
