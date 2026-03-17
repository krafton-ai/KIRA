from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "apps" / "agentd" / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kiraclaw_agentd.mcp_runtime import McpRuntime
from kiraclaw_agentd.scheduler_runtime import SchedulerRuntime
from kiraclaw_agentd.settings import KiraClawSettings


class FakeSessionManager:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def run(self, session_id: str, prompt: str, metadata: dict | None = None, provider=None, model=None):
        self.calls.append({"session_id": session_id, "prompt": prompt, "metadata": metadata or {}})
        return SimpleNamespace(
            state="completed",
            error=None,
            result=SimpleNamespace(final_response="scheduled smoke response"),
        )


class FakeSlackGateway:
    def __init__(self) -> None:
        self.configured = True
        self.messages: list[dict] = []

    async def send_message(self, channel: str, text: str, thread_ts=None) -> None:
        self.messages.append({"channel": channel, "text": text, "thread_ts": thread_ts})


async def main() -> int:
    with tempfile.TemporaryDirectory(prefix="kiraclaw-scheduler-mcp-") as temp_root:
        base = Path(temp_root)
        settings = KiraClawSettings(
            data_dir=base / "data",
            workspace_dir=base / "workspace",
            home_mode="modern",
            slack_enabled=False,
            mcp_enabled=True,
            mcp_scheduler_enabled=True,
        )
        session_manager = FakeSessionManager()
        slack_gateway = FakeSlackGateway()
        mcp_runtime = McpRuntime(settings)
        scheduler_runtime = SchedulerRuntime(settings, session_manager, slack_gateway)

        try:
            await scheduler_runtime.start()
            await mcp_runtime.start()
            add_tool = next(tool for tool in mcp_runtime.tools if tool.name == "add_schedule")
            add_result = add_tool.run(
                name="Smoke schedule",
                schedule_type="date",
                schedule_value=(datetime.now(timezone.utc) + timedelta(seconds=3)).isoformat(),
                user_id="U123",
                text="KIRA, run smoke schedule",
                channel_id="C123",
            )
            await asyncio.sleep(4.5)
            print(
                json.dumps(
                    {
                        "mcp_state": mcp_runtime.state,
                        "tools": mcp_runtime.tool_names,
                        "add_result": add_result,
                        "scheduler_state": scheduler_runtime.state,
                        "session_calls": session_manager.calls,
                        "slack_messages": slack_gateway.messages,
                    },
                    ensure_ascii=False,
                )
            )
            return 0 if session_manager.calls and slack_gateway.messages else 1
        finally:
            await mcp_runtime.stop()
            await scheduler_runtime.stop()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
