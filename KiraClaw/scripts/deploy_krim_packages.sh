#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KRIM_ROOT="$(cd "$ROOT/../../KRIM" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
SDK_DIST="$KRIM_ROOT/packages/krim-sdk/dist"
CLI_DIST="$KRIM_ROOT/packages/krim/dist"

if [[ ! -x "$PYTHON" ]]; then
  echo "KiraClaw virtualenv is missing: $PYTHON" >&2
  exit 1
fi

uv build "$KRIM_ROOT/packages/krim-sdk"
uv build "$KRIM_ROOT/packages/krim"

SDK_WHEEL="$(ls -t "$SDK_DIST"/krim_sdk-*.whl | head -n1)"
CLI_WHEEL="$(ls -t "$CLI_DIST"/krim-*.whl | head -n1)"

if [[ -z "$SDK_WHEEL" || -z "$CLI_WHEEL" ]]; then
  echo "Failed to find freshly built KRIM wheels." >&2
  exit 1
fi

uv pip install \
  --python "$PYTHON" \
  --reinstall \
  "$SDK_WHEEL" \
  "$CLI_WHEEL"

echo "Installed local KRIM wheels into $PYTHON"
