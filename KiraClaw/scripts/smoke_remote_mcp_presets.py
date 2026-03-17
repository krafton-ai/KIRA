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

from kiraclaw_agentd.mcp_runtime import McpRuntime
from kiraclaw_agentd.settings import KiraClawSettings


async def _probe(label: str, **flags: bool) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"kiraclaw-{label}-") as temp_root:
        base = Path(temp_root)
        settings = KiraClawSettings(
            data_dir=base / "data",
            workspace_dir=base / "workspace",
            home_mode="modern",
            slack_enabled=False,
            mcp_enabled=True,
            **flags,
        )
        runtime = McpRuntime(settings)
        try:
            await runtime.start()
            return {
                "label": label,
                "state": runtime.state,
                "servers": runtime.loaded_server_names,
                "tools": runtime.tool_names,
                "error": runtime.last_error,
            }
        finally:
            await runtime.stop()


async def main() -> int:
    results = [
        await _probe("context7", mcp_context7_enabled=True),
        await _probe("arxiv", mcp_arxiv_enabled=True),
        await _probe("youtube-info", mcp_youtube_info_enabled=True),
    ]
    print(json.dumps(results, ensure_ascii=False))
    return 0 if all(result["tools"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
