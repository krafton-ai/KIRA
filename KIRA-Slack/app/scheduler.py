import os
import json
import uuid
import logging
from datetime import datetime

# Scheduler dedicated logger (separate format)
scheduler_logger = logging.getLogger("SCHEDULER")
scheduler_logger.propagate = False  # Don't propagate to parent logger
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
scheduler_logger.addHandler(_handler)
scheduler_logger.setLevel(logging.INFO)
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor

from app.config.settings import get_settings
from app.queueing_extended import enqueue_message

# Scheduler instance and configuration
# =================================================================
# Enable concurrent execution with AsyncIOExecutor
executors = {
    'default': AsyncIOExecutor()
}
job_defaults = {
    'coalesce': False,  # Don't merge accumulated jobs
    'max_instances': 3,  # Same job can run up to 3 instances concurrently
    'misfire_grace_time': 30  # Allow up to 30 seconds delay
}
scheduler = AsyncIOScheduler(executors=executors, job_defaults=job_defaults)
settings = get_settings()
SCHEDULE_DIR = os.path.join(settings.FILESYSTEM_BASE_DIR, "schedule_data")
SCHEDULE_FILE = os.path.join(SCHEDULE_DIR, "schedules.json")


# Internal file I/O and schedule management logic
# =================================================================
def _ensure_dir_and_file():
    os.makedirs(SCHEDULE_DIR, exist_ok=True)
    if not os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def read_schedules_from_file() -> List[Dict[str, Any]]:
    _ensure_dir_and_file()
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def write_schedules_to_file(schedules: List[Dict[str, Any]]):
    _ensure_dir_and_file()
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(schedules, f, indent=2, ensure_ascii=False)


async def scheduled_message_wrapper(message: dict, schedule_id: str, schedule_name: str):
    """
    Wrapper function that executes scheduled messages (with logging and error handling)

    Args:
        message: Message to send
        schedule_id: Schedule ID
        schedule_name: Schedule name
    """
    try:
        scheduler_logger.info(f"🔔 Executing: [{schedule_name}] (ID: {schedule_id})")
        scheduler_logger.info(f"  └─ Channel: {message.get('channel')}, User: {message.get('user')}")
        scheduler_logger.info(f"  └─ Text preview: {message.get('text', '')[:50]}...")

        await enqueue_message(message)

        scheduler_logger.info(f"✅ Executed successfully: [{schedule_name}] (ID: {schedule_id})")
    except Exception as e:
        scheduler_logger.error(f"❌ Execution failed: [{schedule_name}] (ID: {schedule_id})")
        scheduler_logger.error(f"  └─ Error: {type(e).__name__}: {e}")


async def reload_schedules_from_file():
    """Read schedules from file and reload them into the scheduler."""
    try:
        # Only delete jobs registered with scheduled_message_wrapper (keep checkers/suggester)
        jobs = scheduler.get_jobs()
        for job in jobs:
            if job.func == scheduled_message_wrapper:
                scheduler.remove_job(job.id)
                scheduler_logger.debug(f"Removed existing job: {job.name} (ID: {job.id})")
    except Exception as e:
        scheduler_logger.warning(f"Error while deleting existing schedules (normal on first run): {e}")

    schedules = read_schedules_from_file()
    count = 0
    for schedule in schedules:
        if not schedule.get("is_enabled"):
            continue

        try:
            # Add user_id to the message payload
            message = {
                "user": schedule.get("user"),
                "text": schedule.get("text"),
                "channel": schedule.get("channel"),
                "skip_ack_messages": True,  # Skip approval/busy Slack messages for scheduled tasks
            }
            schedule_type = schedule.get("schedule_type")
            schedule_value = schedule.get("schedule_value")
            schedule_id = schedule.get("id")
            schedule_name = schedule.get("name")

            job_args = {
                "id": schedule_id,
                "name": schedule_name,
                "args": [message, schedule_id, schedule_name],  # Pass ID and name to wrapper
            }

            if schedule_type == "cron":
                scheduler.add_job(
                    scheduled_message_wrapper,  # Use wrapper function
                    trigger=CronTrigger.from_crontab(schedule_value),
                    **job_args,
                )
                scheduler_logger.info(f"📅 Registered cron: [{schedule_name}] (ID: {schedule_id}), pattern: {schedule_value}")
            elif schedule_type == "date":
                # Skip if the time is in the past
                try:
                    run_date = datetime.fromisoformat(schedule_value.replace('Z', '+00:00'))
                    if run_date <= datetime.now(run_date.tzinfo):
                        scheduler_logger.info(f"⏭️ Skipping past: [{schedule_name}] (ID: {schedule_id}), time: {schedule_value}")
                        continue
                except (ValueError, AttributeError) as e:
                    scheduler_logger.error(f"❌ Invalid date format: [{schedule_name}] (ID: {schedule_id}), value: {schedule_value}, error: {e}")
                    continue

                scheduler.add_job(
                    scheduled_message_wrapper,  # Use wrapper function
                    trigger="date",
                    run_date=schedule_value,
                    **job_args
                )
                scheduler_logger.info(f"📅 Registered one-time: [{schedule_name}] (ID: {schedule_id}), time: {schedule_value}")

            count += 1
        except Exception as e:
            scheduler_logger.error(f"❌ Failed to register: [{schedule.get('name')}] (ID: {schedule.get('id')}), error: {e}")
    scheduler_logger.info(f"Total {count} schedules reloaded successfully")
