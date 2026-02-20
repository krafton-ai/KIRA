import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

# Per-channel message queues
message_queues: Dict[str, asyncio.Queue] = {}

# Global orchestrator queue (for heavy tasks)
orchestrator_queue = asyncio.Queue(maxsize=100)

# Memory save dedicated queue (single worker for sequential processing)
memory_queue = asyncio.Queue(maxsize=100)

# Orchestrator worker status management
_active_orchestrator_workers = 0  # Currently active worker count
_status_update_lock = asyncio.Lock()  # Prevent duplicate status updates

# Global variables for debounce management
_debounce_timers: Dict[str, asyncio.Task] = {}
_accumulated_messages: Dict[str, list] = {}


def get_or_create_channel_queue(channel_id: str) -> asyncio.Queue:
    """Get or create a per-channel queue"""
    if channel_id not in message_queues:
        message_queues[channel_id] = asyncio.Queue(maxsize=100)
        logging.info(f"[QUEUE] Created new queue for channel: {channel_id}")
    return message_queues[channel_id]


async def enqueue_message(message):
    """Add to per-channel message queue"""
    channel_id = message.get("channel")
    queue = get_or_create_channel_queue(channel_id)
    await queue.put({"message": message})
    logging.info(f"[QUEUE] Message enqueued to channel {channel_id}, queue size: {queue.qsize()}")


async def enqueue_orchestrator_job(orchestrator_job: dict):
    """Add job to global orchestrator queue"""
    await orchestrator_queue.put(orchestrator_job)
    logging.info(f"[ORCHESTRATOR_QUEUE] Job enqueued, queue size: {orchestrator_queue.qsize()}")


async def enqueue_memory_job(memory_job: dict):
    """Add job to memory save queue (sequential processing)"""
    await memory_queue.put(memory_job)
    logging.info(f"[MEMORY_QUEUE] Job enqueued, queue size: {memory_queue.qsize()}")


async def debounced_enqueue_message(message, delay_seconds: float = 2.0):
    """Debounced version of enqueue_message - merges accumulated messages if no additional messages within specified time

    Args:
        message: Slack message object
        delay_seconds: debounce delay time (seconds), 0 for immediate processing
    """
    user_id = message.get("user")
    channel_id = message.get("channel")
    debounce_key = f"{channel_id}:{user_id}"

    # Process immediately if 0 seconds
    if delay_seconds == 0:
        logging.info(f"[DEBOUNCE] Immediate processing for {user_id} in {channel_id} (delay=0)")
        await enqueue_message(message)
        return

    # Accumulate messages
    if debounce_key not in _accumulated_messages:
        _accumulated_messages[debounce_key] = []
        logging.info(f"[DEBOUNCE] First message from {user_id} in {channel_id}, starting {delay_seconds}s timer")
    else:
        logging.info(f"[DEBOUNCE] Additional message from {user_id} in {channel_id}, resetting timer")

    _accumulated_messages[debounce_key].append({
        "message": message,
        "timestamp": datetime.now()
    })

    # Cancel existing timer if present
    if debounce_key in _debounce_timers:
        _debounce_timers[debounce_key].cancel()
        logging.info(f"[DEBOUNCE] Cancelled previous timer for {debounce_key}")

    # Start new timer
    async def delayed_process():
        try:
            await asyncio.sleep(delay_seconds)

            # After timer expires, merge accumulated messages and process
            if debounce_key in _accumulated_messages:
                accumulated = _accumulated_messages[debounce_key]
                message_count = len(accumulated)
                logging.info(f"[DEBOUNCE] Timer expired, merging {message_count} messages from {user_id} in {channel_id}")

                # Merge text from messages
                merged_text_parts = []
                base_message = accumulated[0]["message"].copy()  # Use first message as base

                for msg_data in accumulated:
                    msg = msg_data["message"]
                    text = msg.get("text", "").strip()
                    if text:
                        merged_text_parts.append(text)

                # Create message with merged text
                if merged_text_parts:
                    base_message["text"] = "\n".join(merged_text_parts)
                    logging.info(f"[DEBOUNCE] Merged text: {base_message['text'][:100]}...")

                    # Process actual message
                    await enqueue_message(base_message)
                else:
                    logging.warning(f"[DEBOUNCE] No text content found in {message_count} messages")

                # Cleanup
                del _accumulated_messages[debounce_key]
                if debounce_key in _debounce_timers:
                    del _debounce_timers[debounce_key]

        except asyncio.CancelledError:
            logging.info(f"[DEBOUNCE] Timer cancelled for {debounce_key}")
            raise
        except Exception as e:
            logging.error(f"[DEBOUNCE] Error in delayed processing for {debounce_key}: {e}")
            # Cleanup on error as well
            if debounce_key in _accumulated_messages:
                del _accumulated_messages[debounce_key]
            if debounce_key in _debounce_timers:
                del _debounce_timers[debounce_key]

    # Register new timer
    _debounce_timers[debounce_key] = asyncio.create_task(delayed_process())


def start_channel_workers(app, process_func, workers_per_channel=5):
    """Start per-channel workers - process messages in parallel for each channel"""

    async def channel_worker(channel_id: str, queue: asyncio.Queue, worker_id: int):
        """Worker that processes messages in parallel for a specific channel"""
        client = app.client
        logging.info(f"[CHANNEL_WORKER-{worker_id}] Started worker for channel: {channel_id}")

        while True:
            try:
                job = await queue.get()
                message = job["message"]

                logging.info(f"[CHANNEL_WORKER-{worker_id}] Processing message in {channel_id}, queue size: {queue.qsize()}")
                await process_func(message, client)

            except Exception as e:
                logging.error(f"[CHANNEL_WORKER-{worker_id}] Error in channel {channel_id}: {e}")
            finally:
                queue.task_done()

    async def monitor_and_spawn_workers():
        """Automatically spawn workers when new channel queues are created"""
        monitored_channels = set()

        while True:
            await asyncio.sleep(1)  # Check every second

            for channel_id, queue in list(message_queues.items()):
                if channel_id not in monitored_channels:
                    # New channel found, spawn multiple workers per channel
                    for worker_id in range(workers_per_channel):
                        asyncio.create_task(channel_worker(channel_id, queue, worker_id))
                    monitored_channels.add(channel_id)
                    logging.info(f"[MONITOR] Spawned {workers_per_channel} workers for new channel: {channel_id}")

    loop = asyncio.get_running_loop()
    loop.create_task(monitor_and_spawn_workers())


def start_orchestrator_worker(app, orchestrator_func, num_workers=2):
    """Start global orchestrator worker - process all orchestrator jobs in parallel"""

    async def orchestrator_worker(worker_id: int):
        global _active_orchestrator_workers
        client = app.client
        logging.info(f"[ORCHESTRATOR_WORKER-{worker_id}] Started")

        # Bot status update function
        async def update_bot_status():
            global _active_orchestrator_workers

            # Use lock to prevent concurrent updates
            async with _status_update_lock:
                active_workers = _active_orchestrator_workers
                is_busy = active_workers >= num_workers  # Busy if all workers are active

                logging.info(f"[STATUS] Updating bot status (active_workers: {active_workers}/{num_workers}, is_busy: {is_busy})")
                try:
                    if is_busy:
                        await client.users_profile_set(
                            profile={
                                "status_text": "i'm busy",
                                "status_emoji": ":hourglass_flowing_sand:"
                            }
                        )
                        logging.info(f"[STATUS] Bot status updated to BUSY")
                    else:
                        await client.users_profile_set(
                            profile={
                                "status_text": "",
                                "status_emoji": "",
                                "status_expiration": 0
                            }
                        )
                        logging.info(f"[STATUS] Bot status cleared")
                except Exception as e:
                    if "not_allowed_token_type" in str(e):
                        logging.debug(f"[STATUS] Bot status update not supported with current token type")
                    else:
                        logging.warning(f"[STATUS] Failed to update bot status: {e}")

        while True:
            logging.info(f"[ORCHESTRATOR_WORKER-{worker_id}] Waiting for next job from queue...")
            job = await orchestrator_queue.get()
            logging.info(f"[ORCHESTRATOR_WORKER-{worker_id}] Job received from queue")

            try:
                # Job started - increment active worker count
                _active_orchestrator_workers += 1
                logging.info(f"[ORCHESTRATOR_WORKER-{worker_id}] Started job (active: {_active_orchestrator_workers}/{num_workers})")
                await update_bot_status()

                await orchestrator_func(job, client)
                logging.info(f"[ORCHESTRATOR_WORKER-{worker_id}] Job completed successfully")
            except Exception as e:
                logging.error(f"[ORCHESTRATOR_WORKER-{worker_id}] Error: {e}")
            finally:
                # Job completed - decrement active worker count
                _active_orchestrator_workers -= 1
                orchestrator_queue.task_done()
                logging.info(f"[ORCHESTRATOR_WORKER-{worker_id}] Finished job (active: {_active_orchestrator_workers}/{num_workers})")
                await update_bot_status()

    loop = asyncio.get_running_loop()
    for worker_id in range(num_workers):
        loop.create_task(orchestrator_worker(worker_id))
        logging.info(f"[ORCHESTRATOR_WORKER] Created worker {worker_id}/{num_workers}")


def start_memory_worker(memory_func):
    """Start memory save dedicated worker (single worker for sequential processing)

    Args:
        memory_func: Memory save function (receives and processes job dict)
    """
    async def memory_worker():
        logging.info(f"[MEMORY_WORKER] Started")

        while True:
            logging.info(f"[MEMORY_WORKER] Waiting for next job...")
            job = await memory_queue.get()
            logging.info(f"[MEMORY_WORKER] Job received from queue (queue size: {memory_queue.qsize()})")

            try:
                await memory_func(job)
                logging.info(f"[MEMORY_WORKER] Job completed successfully")
            except Exception as e:
                logging.error(f"[MEMORY_WORKER] Error: {e}")
            finally:
                memory_queue.task_done()

    loop = asyncio.get_running_loop()
    loop.create_task(memory_worker())
    logging.info(f"[MEMORY_WORKER] Created single worker for sequential memory operations")