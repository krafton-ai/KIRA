"""
Email Tasks Database Manager
SQLite database for managing tasks extracted from emails
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
    return db_dir / "email_tasks.db"


def init_db():
    """Initialize database and create tables"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            subject TEXT NOT NULL,
            task_description TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            user TEXT,
            text TEXT,
            channel TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    """)

    conn.commit()
    conn.close()
    logging.info(f"[EMAIL_TASKS_DB] Database initialized at {db_path}")


def add_task(
    email_id: str,
    sender: str,
    subject: str,
    task_description: str,
    priority: str = "medium",
    user_id: Optional[str] = None,
    text: Optional[str] = None,
    channel_id: Optional[str] = None
) -> int:
    """
    Add new task

    Args:
        email_id: Email ID
        sender: Sender
        subject: Email subject
        task_description: Task description
        priority: Priority (low/medium/high)
        user_id: User ID to receive notification
        text: Notification message content
        channel_id: Channel ID to send notification

    Returns:
        ID of created task
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO email_tasks
        (email_id, sender, subject, task_description, priority, user, text, channel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (email_id, sender, subject, task_description, priority, user_id, text, channel_id))

    task_id = cursor.lastrowid
    conn.commit()
    conn.close()

    logging.info(f"[EMAIL_TASKS_DB] Added task {task_id}: {task_description[:50]}...")
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

    cursor.execute("""
        SELECT * FROM email_tasks
        WHERE status = 'pending'
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
            END,
            created_at ASC
        LIMIT ?
    """, (limit,))

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

    cursor.execute("""
        UPDATE email_tasks
        SET status = 'completed'
        WHERE id = ?
    """, (task_id,))

    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected > 0:
        logging.info(f"[EMAIL_TASKS_DB] Completed task {task_id}")
        return True
    else:
        logging.warning(f"[EMAIL_TASKS_DB] Task {task_id} not found")
        return False
