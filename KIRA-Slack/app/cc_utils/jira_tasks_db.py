"""
Jira Tasks Database Manager
SQLite database for managing tasks extracted from Jira
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config.settings import get_settings

settings = get_settings()


def get_db_path() -> Path:
    """Return database file path"""
    base_dir = settings.FILESYSTEM_BASE_DIR or "."
    db_dir = Path(base_dir) / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "jira_tasks.db"


def init_db():
    """Initialize database and create tables"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jira_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_key TEXT NOT NULL,
            issue_url TEXT NOT NULL,
            summary TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            task_description TEXT NOT NULL,
            user TEXT,
            text TEXT,
            channel TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            db_status TEXT DEFAULT 'pending'
        )
    """
    )

    # Add unique index on issue_key (prevent duplicates)
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_issue_key
        ON jira_tasks(issue_key)
    """
    )

    conn.commit()
    conn.close()
    logging.info(f"[JIRA_TASKS_DB] Database initialized at {db_path}")


def add_task(
    issue_key: str,
    issue_url: str,
    summary: str,
    status: str,
    priority: str,
    task_description: str,
    user_id: Optional[str] = None,
    text: Optional[str] = None,
    channel_id: Optional[str] = None,
) -> int:
    """
    Add new task (update if duplicate)

    Args:
        issue_key: Jira issue key (e.g., PROJ-123)
        issue_url: Jira issue URL
        summary: Issue title
        status: Issue status
        priority: Priority (low/medium/high)
        task_description: Task description
        user_id: User ID to receive notification
        text: Notification message content
        channel_id: Channel ID to send notification

    Returns:
        ID of created task
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update if exists, insert if not
    cursor.execute(
        """
        INSERT INTO jira_tasks
        (issue_key, issue_url, summary, status, priority, task_description, user, text, channel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(issue_key) DO UPDATE SET
            issue_url = excluded.issue_url,
            summary = excluded.summary,
            status = excluded.status,
            priority = excluded.priority,
            task_description = excluded.task_description,
            user = excluded.user,
            text = excluded.text,
            channel = excluded.channel,
            updated_at = CURRENT_TIMESTAMP,
            db_status = 'pending'
    """,
        (
            issue_key,
            issue_url,
            summary,
            status,
            priority,
            task_description,
            user_id,
            text,
            channel_id,
        ),
    )

    # lastrowid is the ID of INSERT or UPDATE row
    task_id = cursor.lastrowid

    # Query actual ID in case of UPDATE
    if cursor.rowcount == 1:
        cursor.execute("SELECT id FROM jira_tasks WHERE issue_key = ?", (issue_key,))
        result = cursor.fetchone()
        if result:
            task_id = result[0]

    conn.commit()
    conn.close()

    logging.info(
        f"[JIRA_TASKS_DB] Added/Updated task {task_id}: {issue_key} - {task_description[:50]}..."
    )
    return task_id


def get_pending_tasks(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get list of pending tasks

    Args:
        limit: Maximum number to retrieve

    Returns:
        List of tasks (list of dictionaries)
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM jira_tasks
        WHERE db_status = 'pending'
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
            END,
            created_at ASC
        LIMIT ?
    """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    tasks = [dict(row) for row in rows]
    return tasks


def complete_task(task_id: int) -> bool:
    """
    Mark task as complete (after entering queue)

    Args:
        task_id: Task ID

    Returns:
        Whether successful
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE jira_tasks
        SET db_status = 'completed'
        WHERE id = ?
    """,
        (task_id,),
    )

    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected > 0:
        logging.info(f"[JIRA_TASKS_DB] Completed task {task_id}")
        return True
    else:
        logging.warning(f"[JIRA_TASKS_DB] Task {task_id} not found")
        return False


def get_existing_issue_keys() -> List[str]:
    """
    Return list of issue_keys already existing in DB

    Returns:
        List of issue_keys
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT issue_key FROM jira_tasks")
    rows = cursor.fetchall()
    conn.close()

    issue_keys = [row[0] for row in rows]
    return issue_keys
