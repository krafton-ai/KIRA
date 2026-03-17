from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "apps" / "agentd" / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kiraclaw_agentd.engine import KiraClawEngine
from kiraclaw_agentd.settings import KiraClawSettings


async def main() -> int:
    with tempfile.TemporaryDirectory(prefix="kiraclaw-mcp-") as temp_root:
        base = Path(temp_root)
        settings = KiraClawSettings(
            data_dir=base / "data",
            workspace_dir=base / "workspace",
            home_mode="modern",
            slack_enabled=False,
            mcp_enabled=True,
            mcp_time_enabled=True,
        )

        engine = KiraClawEngine(settings)
        try:
            await engine.start()
            summary = {
                "state": engine.mcp_runtime.state,
                "servers": engine.mcp_runtime.loaded_server_names,
                "tool_count": len(engine.mcp_runtime.tools),
                "tools": engine.mcp_runtime.tool_names,
                "error": engine.mcp_runtime.last_error,
            }
            print(json.dumps(summary, ensure_ascii=False))
            return 0 if engine.mcp_runtime.tools else 1
        finally:
            await engine.stop()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
