from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MemoryWriteRequest:
    session_id: str
    prompt: str
    response: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryIndexEntry:
    path: str
    title: str
    category: str
    summary: str
    updated_at: str
    tags: list[str] = field(default_factory=list)
    source: str = ""
    session_id: str = ""
    user_id: str = ""
    user_name: str = ""
    channel_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "MemoryIndexEntry":
        return cls(
            path=str(value.get("path", "")),
            title=str(value.get("title", "")),
            category=str(value.get("category", "")),
            summary=str(value.get("summary", "")),
            updated_at=str(value.get("updated_at", "")),
            tags=[str(tag) for tag in value.get("tags", []) if str(tag).strip()],
            source=str(value.get("source", "")),
            session_id=str(value.get("session_id", "")),
            user_id=str(value.get("user_id", "")),
            user_name=str(value.get("user_name", "")),
            channel_id=str(value.get("channel_id", "")),
        )
