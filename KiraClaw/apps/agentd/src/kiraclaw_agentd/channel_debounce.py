from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar


T = TypeVar("T")


logger = logging.getLogger(__name__)


class KeyedDebouncer(Generic[T]):
    def __init__(
        self,
        *,
        delay_seconds: float,
        on_flush: Callable[[list[T]], Awaitable[None]],
        label: str,
    ) -> None:
        self.delay_seconds = max(0.0, delay_seconds)
        self._on_flush = on_flush
        self._label = label
        self._pending: dict[str, list[T]] = {}
        self._timers: dict[str, asyncio.Task[None]] = {}

    async def enqueue(self, key: str, item: T) -> None:
        if self.delay_seconds <= 0:
            await self._on_flush([item])
            return

        self._pending.setdefault(key, []).append(item)
        timer = self._timers.get(key)
        if timer is not None:
            timer.cancel()
        self._timers[key] = asyncio.create_task(self._delayed_flush(key), name=f"{self._label}-debounce:{key}")

    async def stop(self) -> None:
        timers = list(self._timers.values())
        self._timers.clear()
        self._pending.clear()
        for timer in timers:
            timer.cancel()
        for timer in timers:
            try:
                await timer
            except asyncio.CancelledError:
                pass

    async def _delayed_flush(self, key: str) -> None:
        try:
            await asyncio.sleep(self.delay_seconds)
            items = self._pending.pop(key, [])
            self._timers.pop(key, None)
            if items:
                await self._on_flush(items)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("%s debounce flush failed for %s: %s", self._label, key, exc)
            self._pending.pop(key, None)
            self._timers.pop(key, None)
