from __future__ import annotations

import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from kiraclaw_agentd.files_mcp_tools import build_files_tool_specs
from kiraclaw_agentd.mcp_stdio import run_mcp_stdio


def main() -> int:
    return run_mcp_stdio(name="files", version="1.0.0", tools=build_files_tool_specs())


if __name__ == "__main__":
    raise SystemExit(main())
