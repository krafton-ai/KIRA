from __future__ import annotations

from kiraclaw_agentd.memory_models import MemoryWriteRequest
from kiraclaw_agentd.memory_store import MemoryStore


def test_memory_store_saves_semantic_memory_to_user_and_channel_files(tmp_path) -> None:
    memory_dir = tmp_path / "memories"
    index_file = memory_dir / "index.json"
    store = MemoryStore(memory_dir, index_file, "지호봇")
    store.ensure_structure()

    store.save_exchange(
        MemoryWriteRequest(
            session_id="slack:dm:D123",
            prompt="Please remember the quarterly roadmap.",
            response="The quarterly roadmap is focused on browser MCP rollout.",
            created_at="2026-03-17T00:00:00+00:00",
            metadata={
                "source": "slack-dm",
                "user": "U123",
                "user_name": "Jiho Jeon",
                "channel": "D123",
            },
        )
    )

    assert (memory_dir / "users" / "U123_Jiho-Jeon.md").exists()
    assert (memory_dir / "channels" / "D123.md").exists()
    assert not (memory_dir / "misc" / "slack-dm-D123.md").exists()
    assert store.file_count == 2


def test_memory_store_saves_episodic_memory_to_session_file_only(tmp_path) -> None:
    memory_dir = tmp_path / "memories"
    index_file = memory_dir / "index.json"
    store = MemoryStore(memory_dir, index_file, "지호봇")
    store.ensure_structure()

    store.save_exchange(
        MemoryWriteRequest(
            session_id="desktop:local",
            prompt="Confluence 연동을 마무리해줘.",
            response="Confluence 연결을 완료했고 기본 페이지 ID도 설정했어.",
            created_at="2026-03-17T00:00:00+00:00",
            metadata={"source": "api"},
            memory_kind="episodic",
            summary="Confluence 연결을 완료했고 기본 페이지 ID도 설정함.",
        )
    )

    assert (memory_dir / "misc" / "desktop-local.md").exists()
    assert store.file_count == 1


def test_memory_store_retrieves_relevant_context_from_saved_files(tmp_path) -> None:
    memory_dir = tmp_path / "memories"
    index_file = memory_dir / "index.json"
    store = MemoryStore(memory_dir, index_file, "KIRA")
    store.ensure_structure()

    store.save_exchange(
        MemoryWriteRequest(
            session_id="desktop:local",
            prompt="We decided to use Playwright for browser tasks.",
            response="Yes, Playwright is the browser MCP path.",
            created_at="2026-03-17T00:00:00+00:00",
            metadata={"source": "desktop"},
        )
    )

    context = store.retrieve_context(
        "What browser MCP did we decide to use?",
        "desktop:local",
        {"source": "desktop"},
    )

    assert context is not None
    assert "Playwright" in context
    assert "<memory_file path=" in context


def test_memory_store_can_save_and_search_manual_notes(tmp_path) -> None:
    memory_dir = tmp_path / "memories"
    index_file = memory_dir / "index.json"
    store = MemoryStore(memory_dir, index_file, "KIRA")
    store.ensure_structure()

    saved_paths = store.save_note(
        session_id="desktop:manual",
        note="Remember that the release checklist must include Telegram smoke tests.",
        metadata={"source": "tool", "user_name": "Jiho"},
        created_at="2026-03-18T00:00:00+00:00",
    )
    rows = store.search(
        "release checklist telegram",
        "desktop:manual",
        {"source": "tool", "user_name": "Jiho"},
    )

    assert saved_paths
    assert rows
    assert rows[0]["path"].endswith(".md")
    assert rows[0]["memory_kind"] == "semantic"
    assert "Telegram smoke tests" in rows[0]["content"]


def test_memory_store_can_upsert_and_search_index_entries(tmp_path) -> None:
    memory_dir = tmp_path / "memories"
    index_file = memory_dir / "index.json"
    store = MemoryStore(memory_dir, index_file, "KIRA")
    store.ensure_structure()

    memory_file = memory_dir / "projects" / "claw-rollout.md"
    memory_file.parent.mkdir(parents=True, exist_ok=True)
    memory_file.write_text("# Claw Rollout\n\nTrack the Telegram launch tasks.\n", encoding="utf-8")

    entry = store.upsert_index_entry(
        path=str(memory_file),
        title="Claw Rollout",
        category="projects",
        summary="Telegram launch tasks and rollout notes.",
        tags=["telegram", "rollout"],
        metadata={"source": "tool", "session_id": "desktop:local"},
        updated_at="2026-03-18T00:00:00+00:00",
    )
    rows = store.search_index("telegram rollout", "desktop:local", {"source": "tool"})

    assert entry["path"] == "projects/claw-rollout.md"
    assert entry["absolute_path"] == str(memory_file.resolve())
    assert rows
    assert rows[0]["path"] == "projects/claw-rollout.md"
    assert rows[0]["exists"] is True
