from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
import inspect
import logging
import time
from typing import Any, Callable
from uuid import uuid4

from kiraclaw_agentd.engine import KiraClawEngine, RunResult
from kiraclaw_agentd.memory_models import MemoryWriteRequest

_CONVERSATION_HISTORY_TURNS = 6
_CONVERSATION_TEXT_CHAR_LIMIT = 1_200

logger = logging.getLogger(__name__)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_watch_metadata(metadata: dict[str, Any] | None) -> bool:
    if not metadata:
        return False
    return str(metadata.get("source", "")).strip().lower() == "watch"


@dataclass
class RunRequest:
    prompt: str
    provider: str | None = None
    model: str | None = None
    context_prefix: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunRecord:
    run_id: str
    session_id: str
    state: str
    prompt: str
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    result: RunResult | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionLane:
    def __init__(
        self,
        session_id: str,
        engine: KiraClawEngine,
        idle_timeout_seconds: float,
        build_context: Callable[[str, str, str | None], str | None],
        build_memory_context: Callable[[str, str, dict[str, Any] | None], str | None],
        on_record_complete: Callable[[RunRecord], Any],
        on_idle: Callable[[str, "SessionLane"], None],
    ) -> None:
        self.session_id = session_id
        self.engine = engine
        self.idle_timeout_seconds = max(0.05, idle_timeout_seconds)
        self._build_context = build_context
        self._build_memory_context = build_memory_context
        self._on_record_complete = on_record_complete
        self._on_idle = on_idle
        self.queue: asyncio.Queue[tuple[RunRecord, asyncio.Future[RunRecord], RunRequest]] = asyncio.Queue()
        self.worker_task: asyncio.Task[None] | None = None
        self.last_activity_monotonic = time.monotonic()

    @property
    def active(self) -> bool:
        return self.worker_task is not None and not self.worker_task.done()

    def touch(self) -> None:
        self.last_activity_monotonic = time.monotonic()

    def ensure_worker(self) -> None:
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker(), name=f"session-lane:{self.session_id}")

    async def enqueue(self, request: RunRequest, record: RunRecord) -> RunRecord:
        self.touch()
        self.ensure_worker()
        future: asyncio.Future[RunRecord] = asyncio.get_running_loop().create_future()
        await self.queue.put((record, future, request))
        return await future

    async def _worker(self) -> None:
        try:
            while True:
                try:
                    record, future, request = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=self.idle_timeout_seconds,
                    )
                except asyncio.TimeoutError:
                    if self.queue.empty():
                        break
                    continue

                self.touch()
                try:
                    record.state = "running"
                    record.started_at = utc_now()
                    conversation_context = self._build_context(
                        self.session_id,
                        record.run_id,
                        request.context_prefix,
                    )
                    memory_context = self._build_memory_context(
                        request.prompt,
                        self.session_id,
                        request.metadata,
                    )
                    result = await asyncio.to_thread(
                        self.engine.run,
                        request.prompt,
                        request.provider,
                        request.model,
                        conversation_context,
                        memory_context,
                    )
                    record.result = result
                    record.state = "completed"
                    record.finished_at = utc_now()
                    maybe_result = self._on_record_complete(record)
                    if inspect.isawaitable(maybe_result):
                        await maybe_result
                    if not future.done():
                        future.set_result(record)
                except Exception as exc:
                    record.error = str(exc)
                    record.state = "failed"
                    record.finished_at = utc_now()
                    if not future.done():
                        future.set_result(record)
                finally:
                    self.touch()
                    self.queue.task_done()
        except asyncio.CancelledError:
            while not self.queue.empty():
                try:
                    record, future, _request = self.queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                record.error = "Session lane was stopped before the run could start."
                record.state = "failed"
                record.finished_at = utc_now()
                if not future.done():
                    future.set_result(record)
                self.queue.task_done()
            raise
        finally:
            self.worker_task = None
            self.touch()
            self._on_idle(self.session_id, self)

    async def stop(self) -> None:
        task = self.worker_task
        if task is None or task.done():
            self.worker_task = None
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


class SessionManager:
    def __init__(
        self,
        engine: KiraClawEngine,
        memory_context_provider: Callable[[str, str, dict[str, Any]], str | None] | None = None,
        on_record_complete: Callable[[MemoryWriteRequest], Any] | None = None,
    ) -> None:
        self.engine = engine
        self.record_limit = max(1, engine.settings.session_record_limit)
        self.idle_timeout_seconds = max(0.05, engine.settings.session_idle_seconds)
        self.memory_context_provider = memory_context_provider
        self.on_record_complete = on_record_complete
        self._lanes: dict[str, SessionLane] = {}
        self._records: dict[str, list[RunRecord]] = {}

    def _append_record(self, session_id: str, record: RunRecord) -> None:
        records = self._records.setdefault(session_id, [])
        records.append(record)
        if len(records) > self.record_limit:
            self._records[session_id] = records[-self.record_limit:]

    def _release_lane(self, session_id: str, lane: SessionLane) -> None:
        current_lane = self._lanes.get(session_id)
        if current_lane is lane and lane.queue.empty() and not lane.active:
            self._lanes.pop(session_id, None)

    def _build_conversation_context(
        self,
        session_id: str,
        current_run_id: str,
        context_prefix: str | None = None,
    ) -> str | None:
        records = self._records.get(session_id, [])

        recent_turns: list[RunRecord] = []
        for record in records:
            if record.run_id == current_run_id:
                continue
            if record.state != "completed" or record.result is None:
                continue
            if not record.prompt.strip() or not record.result.final_response.strip():
                continue
            recent_turns.append(record)

        parts: list[str] = []
        if context_prefix:
            parts.append(context_prefix)

        if recent_turns:
            recent_turns = recent_turns[-_CONVERSATION_HISTORY_TURNS:]
            lines = [
                "Recent KiraClaw session history (oldest first). Use it as context only when it helps continue the same conversation:",
            ]
            for record in recent_turns:
                lines.append(f"User: {_clip_conversation_text(record.prompt)}")
                lines.append(f"Assistant: {_clip_conversation_text(record.result.final_response)}")
            parts.append("\n".join(lines))

        return "\n\n".join(parts) if parts else None

    def _build_memory_context(
        self,
        prompt: str,
        session_id: str,
        metadata: dict[str, Any] | None,
    ) -> str | None:
        if self.memory_context_provider is None or _is_watch_metadata(metadata):
            return None
        try:
            return self.memory_context_provider(prompt, session_id, metadata or {})
        except Exception as exc:
            logger.warning("Memory context retrieval failed for %s: %s", session_id, exc)
            return None

    async def _notify_record_complete(self, record: RunRecord) -> None:
        if (
            self.on_record_complete is None
            or record.state != "completed"
            or record.result is None
            or _is_watch_metadata(record.metadata)
        ):
            return
        request = MemoryWriteRequest(
            session_id=record.session_id,
            prompt=record.prompt,
            response=record.result.final_response,
            created_at=record.finished_at or record.created_at,
            metadata=record.metadata,
        )
        try:
            maybe_result = self.on_record_complete(request)
            if inspect.isawaitable(maybe_result):
                await maybe_result
        except Exception as exc:
            logger.warning("Memory save enqueue failed for %s: %s", record.run_id, exc)

    def _get_lane(self, session_id: str) -> SessionLane:
        lane = self._lanes.get(session_id)
        if lane is None:
            lane = SessionLane(
                session_id=session_id,
                engine=self.engine,
                idle_timeout_seconds=self.idle_timeout_seconds,
                build_context=self._build_conversation_context,
                build_memory_context=self._build_memory_context,
                on_record_complete=self._notify_record_complete,
                on_idle=self._release_lane,
            )
            self._lanes[session_id] = lane
        return lane

    async def run(
        self,
        session_id: str,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        context_prefix: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RunRecord:
        lane = self._get_lane(session_id)
        record = RunRecord(
            run_id=str(uuid4()),
            session_id=session_id,
            state="queued",
            prompt=prompt,
            created_at=utc_now(),
            metadata=metadata or {},
        )
        self._append_record(session_id, record)
        return await lane.enqueue(
            RunRequest(
                prompt=prompt,
                provider=provider,
                model=model,
                context_prefix=context_prefix,
                metadata=metadata or {},
            ),
            record,
        )

    def list_sessions(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        session_ids = sorted(set(self._records.keys()) | set(self._lanes.keys()))
        for session_id in session_ids:
            lane = self._lanes.get(session_id)
            records = self._records.get(session_id, [])
            latest = records[-1] if records else None
            rows.append(
                {
                    "session_id": session_id,
                    "queued_runs": lane.queue.qsize() if lane is not None else 0,
                    "active": lane.active if lane is not None else False,
                    "latest_state": latest.state if latest else None,
                    "latest_run_id": latest.run_id if latest else None,
                    "latest_finished_at": latest.finished_at if latest else None,
                }
            )
        return rows

    def get_session_records(self, session_id: str) -> list[RunRecord]:
        return list(self._records.get(session_id, []))

    async def stop(self) -> None:
        lanes = list(self._lanes.values())
        for lane in lanes:
            await lane.stop()
        self._lanes.clear()


def _clip_conversation_text(text: str) -> str:
    stripped = " ".join(text.strip().split())
    if len(stripped) <= _CONVERSATION_TEXT_CHAR_LIMIT:
        return stripped
    return stripped[: _CONVERSATION_TEXT_CHAR_LIMIT - 1].rstrip() + "…"
