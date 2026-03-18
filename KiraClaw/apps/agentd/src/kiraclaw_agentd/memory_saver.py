from __future__ import annotations

from kiraclaw_agentd.memory_models import MemoryWriteRequest
from kiraclaw_agentd.memory_store import MemoryStore


class MemorySaver:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def save(self, request: MemoryWriteRequest) -> None:
        self.store.save_exchange(request)

    def save_note(
        self,
        session_id: str,
        note: str,
        metadata: dict[str, object] | None = None,
        created_at: str | None = None,
    ) -> list[str]:
        return self.store.save_note(
            session_id=session_id,
            note=note,
            metadata=metadata,
            created_at=created_at,
        )

    def save_index_entry(
        self,
        *,
        path: str,
        title: str | None = None,
        category: str | None = None,
        summary: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, object] | None = None,
        updated_at: str | None = None,
    ) -> dict[str, object]:
        return self.store.upsert_index_entry(
            path=path,
            title=title,
            category=category,
            summary=summary,
            tags=tags,
            metadata=metadata,
            updated_at=updated_at,
        )
