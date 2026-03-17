from __future__ import annotations

import asyncio
import base64
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


def _tool_by_name(engine: KiraClawEngine, name: str):
    return next(tool for tool in engine.mcp_runtime.tools if tool.name == name)


async def main() -> int:
    with tempfile.TemporaryDirectory(prefix="kiraclaw-files-mcp-") as temp_root:
        base = Path(temp_root)
        settings = KiraClawSettings(
            data_dir=base / "data",
            workspace_dir=base / "workspace",
            home_mode="modern",
            slack_enabled=False,
            mcp_enabled=True,
            mcp_files_enabled=True,
        )

        engine = KiraClawEngine(settings)
        try:
            await engine.start()
            save_tool = _tool_by_name(engine, "save_base64_image")
            read_tool = _tool_by_name(engine, "read_file_as_base64")
            binary = b"hello-files-mcp"
            saved = save_tool.run(
                file_path="files/C123/hello.bin",
                base64_data=base64.b64encode(binary).decode("utf-8"),
            )
            loaded = read_tool.run(file_path="files/C123/hello.bin")
            print(
                json.dumps(
                    {
                        "state": engine.mcp_runtime.state,
                        "tools": engine.mcp_runtime.tool_names,
                        "saved": saved,
                        "loaded": loaded,
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        finally:
            await engine.stop()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
