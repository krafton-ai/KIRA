"""
Waiting Answer SQLite Database Manager
SQLite database for managing pending response queries
"""

import sqlite3
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
    return db_dir / "waiting_answers.db"


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
        CREATE TABLE IF NOT EXISTS waiting_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            requester_id TEXT NOT NULL,
            requester_name TEXT,
            request_content TEXT NOT NULL,
            respondent_user_id TEXT NOT NULL,
            respondent_name TEXT,
            responded INTEGER DEFAULT 0,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'in_progress'
        )
    """)

    # Add columns to existing table (migration)
    try:
        cursor.execute("ALTER TABLE waiting_answers ADD COLUMN requester_name TEXT")
    except:
        pass  # Ignore if already exists

    try:
        cursor.execute("ALTER TABLE waiting_answers ADD COLUMN respondent_name TEXT")
    except:
        pass  # Ignore if already exists

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_request_id
        ON waiting_answers(request_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_respondent
        ON waiting_answers(respondent_user_id, responded)
    """)

    conn.commit()
    conn.close()


def add_request(
    request_id: str,
    channel_id: str,
    requester_id: str,
    requester_name: str,
    request_content: str,
    respondents: List[Dict[str, str]]
) -> int:
    """
    Add new query (to multiple respondents)

    Args:
        request_id: Unique query ID
        channel_id: Channel ID where query was created
        requester_id: Requester Slack User ID
        requester_name: Requester name
        request_content: Query content
        respondents: List of respondent info [{"user_id": "U123", "name": "John"}, ...]

    Returns:
        Number of records added
    """
    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().isoformat()

    for respondent in respondents:
        respondent_user_id = respondent.get("user_id")
        respondent_name = respondent.get("name", "")

        cursor.execute("""
            INSERT INTO waiting_answers (
                request_id, channel_id, requester_id, requester_name, request_content,
                respondent_user_id, respondent_name, responded, response, created_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, 'in_progress')
        """, (request_id, channel_id, requester_id, requester_name, request_content,
              respondent_user_id, respondent_name, created_at))

    conn.commit()
    count = len(respondents)
    conn.close()

    return count


def get_user_pending_requests(user_id: str) -> List[Dict[str, Any]]:
    """
    Get pending queries for a specific user (within last 24 hours)

    Args:
        user_id: Respondent Slack User ID

    Returns:
        List of pending queries (within last 24 hours)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, request_id, channel_id, requester_id, requester_name, request_content,
            respondent_user_id, respondent_name, responded, response, created_at, updated_at, status
        FROM waiting_answers
        WHERE respondent_user_id = ? AND responded = 0
          AND created_at >= datetime('now', '-1 day')
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def update_response(
    request_id: str,
    user_id: str,
    response: str
) -> bool:
    """
    Update response for a specific query

    Args:
        request_id: Query ID
        user_id: Respondent User ID
        response: Response content

    Returns:
        Whether update was successful
    """
    conn = get_connection()
    cursor = conn.cursor()

    updated_at = datetime.now().isoformat()

    cursor.execute("""
        UPDATE waiting_answers
        SET responded = 1,
            response = ?,
            updated_at = ?,
            status = 'completed'
        WHERE request_id = ? AND respondent_user_id = ?
    """, (response, updated_at, request_id, user_id))

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()

    return success


def get_request_by_id(request_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get specific query (for a specific user)

    Args:
        request_id: Query ID
        user_id: Respondent User ID

    Returns:
        Query info or None
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, request_id, channel_id, requester_id, requester_name, request_content,
            respondent_user_id, respondent_name, responded, response, created_at, updated_at, status
        FROM waiting_answers
        WHERE request_id = ? AND respondent_user_id = ?
    """, (request_id, user_id))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_all_responses_for_request(request_id: str) -> List[Dict[str, Any]]:
    """
    Get all respondents' responses for a specific query

    Args:
        request_id: Query ID

    Returns:
        List of all respondents' responses
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, request_id, channel_id, requester_id, requester_name, request_content,
            respondent_user_id, respondent_name, responded, response, created_at, updated_at, status
        FROM waiting_answers
        WHERE request_id = ?
        ORDER BY created_at ASC
    """, (request_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_request_progress(request_id: str) -> Dict[str, int]:
    """
    Get progress for a specific query

    Args:
        request_id: Query ID

    Returns:
        {"total": Total respondent count, "completed": Completed response count}
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(responded) as completed
        FROM waiting_answers
        WHERE request_id = ?
    """, (request_id,))

    row = cursor.fetchone()
    conn.close()

    return {
        "total": row["total"] if row else 0,
        "completed": row["completed"] if row and row["completed"] else 0
    }
