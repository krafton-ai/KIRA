from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kiraclaw_agentd.memory_models import MemoryIndexEntry, MemoryWriteRequest

_MEMORY_BODY_CHAR_LIMIT = 1_200
_MEMORY_RETRIEVAL_FILE_LIMIT = 4


class MemoryStore:
    def __init__(self, memory_dir: Path, index_file: Path, agent_name: str) -> None:
        self.memory_dir = memory_dir
        self.index_file = index_file
        self.agent_name = agent_name

    @property
    def file_count(self) -> int:
        return len(self._load_index())

    def ensure_structure(self) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        for category in ("users", "channels", "misc"):
            (self.memory_dir / category).mkdir(parents=True, exist_ok=True)
        if not self.index_file.exists():
            self._write_index([])

    def retrieve_context(
        self,
        query: str,
        session_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        metadata = metadata or {}
        index_entries = self._load_index()
        if not index_entries:
            return None

        selected_paths: list[str] = []
        selected_entries: list[MemoryIndexEntry] = []

        def add_entry(entry: MemoryIndexEntry) -> None:
            if entry.path in selected_paths:
                return
            selected_paths.append(entry.path)
            selected_entries.append(entry)

        user_id = str(metadata.get("user", "")).strip()
        channel_id = str(metadata.get("channel", "")).strip()

        for entry in index_entries:
            if user_id and entry.user_id == user_id:
                add_entry(entry)
            elif channel_id and entry.channel_id == channel_id:
                add_entry(entry)
            elif session_id and entry.session_id == session_id and entry.category == "misc":
                add_entry(entry)

        for entry in self._score_entries(query, session_id, metadata, index_entries):
            add_entry(entry)
            if len(selected_entries) >= _MEMORY_RETRIEVAL_FILE_LIMIT:
                break

        if not selected_entries:
            return None

        parts = [
            "Relevant long-term memory from local files. Use it only when it helps with the current request:",
        ]
        for entry in selected_entries[:_MEMORY_RETRIEVAL_FILE_LIMIT]:
            file_path = self.memory_dir / entry.path
            if not file_path.exists():
                continue
            text = file_path.read_text(encoding="utf-8")
            parts.append(f'<memory_file path="{entry.path}">')
            parts.append(_clip_memory_body(text))
            parts.append("</memory_file>")

        return "\n".join(parts) if len(parts) > 1 else None

    def save_exchange(self, request: MemoryWriteRequest) -> None:
        self.ensure_structure()
        now = request.created_at or _utc_now()
        note = self._build_note(request, now)
        entries = self._load_index()

        for target in self._target_files(request):
            relative_path = target["path"]
            file_path = self.memory_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            title = target["title"]
            category = target["category"]
            tags = target["tags"]
            metadata = {
                "title": title,
                "category": category,
                "updated_at": now,
                "source": str(request.metadata.get("source", "")),
                "session_id": request.session_id,
                "user_id": str(request.metadata.get("user", "")),
                "user_name": str(request.metadata.get("user_name", "")),
                "channel_id": str(request.metadata.get("channel", "")),
                "tags": tags,
            }
            self._append_note(file_path, metadata, note)
            entries = self._upsert_index_entry(
                entries,
                MemoryIndexEntry(
                    path=relative_path,
                    title=title,
                    category=category,
                    summary=_clip_inline(
                        f"User: {request.prompt} | Assistant: {request.response}",
                        220,
                    ),
                    updated_at=now,
                    tags=tags,
                    source=str(request.metadata.get("source", "")),
                    session_id=request.session_id,
                    user_id=str(request.metadata.get("user", "")),
                    user_name=str(request.metadata.get("user_name", "")),
                    channel_id=str(request.metadata.get("channel", "")),
                ),
            )

        self._write_index(entries)

    def _score_entries(
        self,
        query: str,
        session_id: str,
        metadata: dict[str, Any],
        entries: list[MemoryIndexEntry],
    ) -> list[MemoryIndexEntry]:
        query_tokens = _tokenize(query)
        scored: list[tuple[int, MemoryIndexEntry]] = []
        user_id = str(metadata.get("user", "")).strip()
        channel_id = str(metadata.get("channel", "")).strip()

        for entry in entries:
            score = 0
            haystack = " ".join(
                [
                    entry.title,
                    entry.summary,
                    " ".join(entry.tags),
                    entry.user_name,
                    entry.channel_id,
                    entry.session_id,
                ]
            ).lower()
            for token in query_tokens:
                if token in haystack:
                    score += 3
            if user_id and entry.user_id == user_id:
                score += 2
            if channel_id and entry.channel_id == channel_id:
                score += 2
            if session_id and entry.session_id == session_id:
                score += 1
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda item: (item[0], item[1].updated_at), reverse=True)
        return [entry for _, entry in scored]

    def _target_files(self, request: MemoryWriteRequest) -> list[dict[str, Any]]:
        metadata = request.metadata
        targets: list[dict[str, Any]] = []

        user_name = str(metadata.get("user_name", "")).strip()
        user_id = str(metadata.get("user", "")).strip()
        if user_name or user_id:
            user_stem = _build_entity_stem(user_id, user_name, fallback="user")
            targets.append(
                {
                    "path": f"users/{user_stem}.md",
                    "title": f"User Memory: {user_name or user_id}",
                    "category": "users",
                    "tags": ["user", "slack" if str(metadata.get("source", "")).startswith("slack") else "desktop"],
                }
            )

        channel_id = str(metadata.get("channel", "")).strip()
        if channel_id:
            channel_stem = _build_entity_stem(channel_id, "", fallback="channel")
            targets.append(
                {
                    "path": f"channels/{channel_stem}.md",
                    "title": f"Channel Memory: {channel_id}",
                    "category": "channels",
                    "tags": ["channel", "slack"],
                }
            )

        session_stem = _slugify(request.session_id) or "session"
        targets.append(
            {
                "path": f"misc/{session_stem}.md",
                "title": f"Session Memory: {request.session_id}",
                "category": "misc",
                "tags": ["session", str(metadata.get("source", "local")) or "local"],
            }
        )
        return targets

    def _append_note(self, file_path: Path, metadata: dict[str, Any], note: str) -> None:
        frontmatter, body = self._read_document(file_path)
        merged = dict(frontmatter)
        merged.update({key: value for key, value in metadata.items() if value})
        merged["updated_at"] = metadata["updated_at"]
        existing_tags = _normalize_tags(frontmatter.get("tags", []))
        merged["tags"] = sorted(set(existing_tags + _normalize_tags(metadata.get("tags", []))))

        if note in body:
            content_body = body
        else:
            content_body = f"{body.rstrip()}\n\n{note}".strip()
        document = f"{_format_frontmatter(merged)}\n\n{content_body}\n"
        file_path.write_text(document, encoding="utf-8")

    def _read_document(self, file_path: Path) -> tuple[dict[str, Any], str]:
        if not file_path.exists():
            return {}, ""

        raw = file_path.read_text(encoding="utf-8")
        if not raw.startswith("---\n"):
            return {}, raw.strip()

        parts = raw.split("---\n", 2)
        if len(parts) < 3:
            return {}, raw.strip()
        frontmatter = _parse_frontmatter(parts[1])
        body = parts[2].strip()
        return frontmatter, body

    def _build_note(self, request: MemoryWriteRequest, created_at: str) -> str:
        summary_prompt = _clip_inline(request.prompt, 280)
        summary_response = _clip_inline(request.response, 520)
        return (
            f"### {created_at}\n"
            f"- User: {summary_prompt}\n"
            f"- {self.agent_name}: {summary_response}"
        )

    def _load_index(self) -> list[MemoryIndexEntry]:
        if not self.index_file.exists():
            return []
        raw = self.index_file.read_text(encoding="utf-8").strip()
        if not raw:
            return []
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return []
        return [MemoryIndexEntry.from_dict(item) for item in payload if isinstance(item, dict)]

    def _write_index(self, entries: list[MemoryIndexEntry]) -> None:
        payload = [entry.to_dict() for entry in sorted(entries, key=lambda item: item.updated_at, reverse=True)]
        self.index_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _upsert_index_entry(
        self,
        entries: list[MemoryIndexEntry],
        new_entry: MemoryIndexEntry,
    ) -> list[MemoryIndexEntry]:
        filtered = [entry for entry in entries if entry.path != new_entry.path]
        filtered.append(new_entry)
        return filtered


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z가-힣._-]+", "-", value.strip())
    slug = slug.strip("-._")
    return slug[:80]


def _build_entity_stem(identifier: str, name: str, fallback: str) -> str:
    identifier_part = _slugify(identifier)
    name_part = _slugify(name)
    if identifier_part and name_part:
        return f"{identifier_part}_{name_part}"
    if identifier_part:
        return identifier_part
    if name_part:
        return name_part
    return fallback


def _normalize_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _format_frontmatter(values: dict[str, Any]) -> str:
    ordered_keys = [
        "title",
        "category",
        "updated_at",
        "source",
        "session_id",
        "user_id",
        "user_name",
        "channel_id",
        "tags",
    ]
    lines = ["---"]
    for key in ordered_keys:
        value = values.get(key)
        if value in (None, "", []):
            continue
        if key == "tags":
            lines.append(f"{key}: {', '.join(_normalize_tags(value))}")
            continue
        escaped = str(value).replace('"', '\\"')
        lines.append(f'{key}: "{escaped}"')
    lines.append("---")
    return "\n".join(lines)


def _parse_frontmatter(raw: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        cleaned = value.strip()
        if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
            cleaned = cleaned[1:-1]
        if key.strip() == "tags":
            values[key.strip()] = _normalize_tags(cleaned)
        else:
            values[key.strip()] = cleaned
    return values


def _clip_inline(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _clip_memory_body(text: str) -> str:
    normalized = text.strip()
    if len(normalized) <= _MEMORY_BODY_CHAR_LIMIT:
        return normalized
    return normalized[-_MEMORY_BODY_CHAR_LIMIT :].lstrip()


def _tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[0-9A-Za-z가-힣_-]{2,}", text)]
    seen: set[str] = set()
    unique: list[str] = []
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        unique.append(token)
    return unique[:12]
