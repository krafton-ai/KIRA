from __future__ import annotations

from kiraclaw_agentd.memory_models import MemoryWriteRequest
from kiraclaw_agentd.memory_store import MemoryStore


def test_memory_store_saves_user_channel_and_session_files(tmp_path) -> None:
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
    assert (memory_dir / "misc" / "slack-dm-D123.md").exists()
    assert store.file_count == 3


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
