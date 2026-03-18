from __future__ import annotations

import asyncio
import contextlib
import logging

from kiraclaw_agentd.memory_models import MemoryWriteRequest
from kiraclaw_agentd.memory_retriever import MemoryRetriever
from kiraclaw_agentd.memory_saver import MemorySaver
from kiraclaw_agentd.memory_store import MemoryStore
from kiraclaw_agentd.settings import KiraClawSettings

logger = logging.getLogger(__name__)


class MemoryRuntime:
    def __init__(self, settings: KiraClawSettings) -> None:
        self.settings = settings
        self.store = MemoryStore(settings.memory_dir, settings.memory_index_file, settings.agent_name)
        self.retriever = MemoryRetriever(self.store)
        self.saver = MemorySaver(self.store)
        self.queue: asyncio.Queue[MemoryWriteRequest] = asyncio.Queue(maxsize=200)
        self.worker_task: asyncio.Task[None] | None = None
        self.state: str = "disabled" if not settings.memory_enabled else "stopped"
        self.last_error: str | None = None

    async def start(self) -> None:
        if not self.settings.memory_enabled:
            self.state = "disabled"
            return

        self.store.ensure_structure()
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker(), name="memory-runtime")
        self.state = "running"
        self.last_error = None

    async def stop(self) -> None:
        task = self.worker_task
        if task is not None and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self.worker_task = None
        if self.settings.memory_enabled:
            self.state = "stopped"
        else:
            self.state = "disabled"

    def build_context(
        self,
        prompt: str,
        session_id: str,
        metadata: dict[str, object] | None = None,
    ) -> str | None:
        if not self.settings.memory_enabled:
            return None
        try:
            return self.retriever.build_context(prompt, session_id, metadata)
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("Memory retrieval failed: %s", exc)
            return None

    async def enqueue_save(self, request: MemoryWriteRequest) -> None:
        if not self.settings.memory_enabled:
            return
        await self.queue.put(request)

    async def _worker(self) -> None:
        try:
            while True:
                request = await self.queue.get()
                try:
                    self.saver.save(request)
                    self.last_error = None
                except Exception as exc:
                    self.last_error = str(exc)
                    logger.error("Memory save failed: %s", exc)
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            raise

    @property
    def queued_count(self) -> int:
        return self.queue.qsize()

    @property
    def file_count(self) -> int:
        return self.store.file_count
