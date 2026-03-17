#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KRIM_ROOT="$(cd "$ROOT/../../KRIM" && pwd)"

PYENV_VERSION=3.12.11 pyenv exec python "$KRIM_ROOT/packages/krim-sdk/test_sdk.py"
PYTHONPATH="$KRIM_ROOT/packages/krim/src:$KRIM_ROOT/packages/krim-sdk/src" \
  uv run --with pytest --with rich --with anthropic --with openai --python 3.12 \
  python -m pytest -q "$KRIM_ROOT/packages/krim/tests"
"$ROOT/scripts/deploy_krim_packages.sh"
"$ROOT/.venv/bin/python" -m pytest -q "$ROOT/tests"

if [[ "${KIRACLAW_RUN_MCP_SMOKES:-0}" == "1" ]]; then
  "$ROOT/.venv/bin/python" "$ROOT/scripts/smoke_time_mcp.py"
  "$ROOT/.venv/bin/python" "$ROOT/scripts/smoke_files_mcp.py"
  "$ROOT/.venv/bin/python" "$ROOT/scripts/smoke_scheduler_mcp.py"
fi

if [[ "${KIRACLAW_RUN_REMOTE_MCP_SMOKES:-0}" == "1" ]]; then
  "$ROOT/.venv/bin/python" "$ROOT/scripts/smoke_remote_mcp_presets.py"
fi
