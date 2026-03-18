#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESKTOP_DIR="$ROOT_DIR/apps/desktop"
DIST_DIR="$DESKTOP_DIR/dist"
APP_BUNDLE="$DIST_DIR/mac-arm64/KIRA.app"
RESOURCES_DIR="$APP_BUNDLE/Contents/Resources"

cd "$ROOT_DIR"

echo "[bridge] verifying local prerequisites"
for cmd in node npm; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[bridge] missing required command: $cmd" >&2
    exit 1
  fi
done

echo "[bridge] validating bridge config"
node <<'NODE' "$DESKTOP_DIR/electron-builder.bridge.json"
const fs = require("fs");
const configPath = process.argv[1];
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));

function assert(condition, message) {
  if (!condition) {
    console.error(`[bridge] ${message}`);
    process.exit(1);
  }
}

assert(config.appId === "com.krafton.kira", "bridge appId must preserve com.krafton.kira");
assert(config.productName === "KIRA", "bridge productName must preserve KIRA");
assert(config.publish?.provider === "s3", "bridge publish provider must stay s3");
assert(config.publish?.bucket === "kira-releases", "bridge publish bucket must stay kira-releases");
assert(Array.isArray(config.extraResources), "bridge extraResources must be present");
NODE

echo "[bridge] running desktop syntax checks"
node --check "$DESKTOP_DIR/main.js"
node --check "$DESKTOP_DIR/preload.js"
node --check "$DESKTOP_DIR/renderer/app/index.mjs"
node --check "$DESKTOP_DIR/renderer/app/chat.mjs"
node --check "$DESKTOP_DIR/renderer/app/home.mjs"
node --check "$DESKTOP_DIR/renderer/app/logs.mjs"
node --check "$DESKTOP_DIR/renderer/app/schedules.mjs"
node --check "$DESKTOP_DIR/renderer/app/settings.mjs"
node --check "$DESKTOP_DIR/renderer/app/skills.mjs"
node --check "$DESKTOP_DIR/renderer/app/state.mjs"

echo "[bridge] running KiraClaw test suite"
if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
  if ! command -v uv >/dev/null 2>&1; then
    echo "[bridge] missing KiraClaw virtualenv and uv is not installed" >&2
    exit 1
  fi
  echo "[bridge] bootstrapping python environment with uv"
  (cd "$ROOT_DIR" && uv sync --extra dev)
fi
"$ROOT_DIR/.venv/bin/python" -m pytest -q

echo "[bridge] building smoke bridge app"
rm -rf "$DIST_DIR"
npm --prefix "$DESKTOP_DIR" run build:bridge:smoke:dir

echo "[bridge] checking packaged bridge layout"
for path in \
  "$APP_BUNDLE" \
  "$RESOURCES_DIR/app.asar" \
  "$RESOURCES_DIR/kiraclaw/pyproject.toml" \
  "$RESOURCES_DIR/kiraclaw/uv.lock" \
  "$RESOURCES_DIR/kiraclaw/apps/agentd/src"
do
  if [[ ! -e "$path" ]]; then
    echo "[bridge] missing packaged resource: $path" >&2
    exit 1
  fi
done

echo "[bridge] smoke bridge verification passed"
