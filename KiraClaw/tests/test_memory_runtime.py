from __future__ import annotations

import asyncio

from kiraclaw_agentd.memory_models import MemoryWriteRequest
from kiraclaw_agentd.memory_runtime import MemoryRuntime
from kiraclaw_agentd.settings import KiraClawSettings


def test_memory_runtime_uses_retriever_and_saver_layers(tmp_path) -> None:
    async def scenario() -> None:
        settings = KiraClawSettings(
            data_dir=tmp_path / "data",
            workspace_dir=tmp_path / "workspace",
            home_mode="modern",
            slack_enabled=False,
        )
        runtime = MemoryRuntime(settings)
        calls: list[tuple[str, object]] = []

        def fake_build_context(prompt: str, session_id: str, metadata=None):
            calls.append(("retrieve", (prompt, session_id, metadata)))
            return "Retrieved memory"

        def fake_save(request: MemoryWriteRequest):
            calls.append(("save", request))

        runtime.retriever.build_context = fake_build_context  # type: ignore[method-assign]
        runtime.saver.save = fake_save  # type: ignore[method-assign]

        await runtime.start()
        context = runtime.build_context("hello", "desktop:local", {"source": "api"})
        await runtime.enqueue_save(
            MemoryWriteRequest(
                session_id="desktop:local",
                prompt="hello",
                response="world",
                created_at="2026-03-18T00:00:00Z",
                metadata={"source": "api"},
            )
        )
        await asyncio.wait_for(runtime.queue.join(), timeout=3)
        await runtime.stop()

        assert context == "Retrieved memory"
        assert calls[0][0] == "retrieve"
        assert calls[1][0] == "save"

    asyncio.run(scenario())
