from __future__ import annotations

import json
import logging
import os
import re
import shutil
import sys
import threading
from pathlib import Path

from krim.mcp import McpServer, McpServerConfig

from kiraclaw_agentd.settings import KiraClawSettings

logger = logging.getLogger(__name__)

_MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_MCP_SERVER_START_TIMEOUT = 12.0
EXTERNAL_MCP_SERVER_START_TIMEOUT = 60.0
PLAYWRIGHT_MCP_SERVER_START_TIMEOUT = 90.0
FILES_MCP_COMMAND = [sys.executable, str(_MODULE_DIR / "files_mcp_server.py")]
SCHEDULER_MCP_COMMAND = [sys.executable, str(_MODULE_DIR / "scheduler_mcp_server.py")]
SLACK_RETRIEVE_MCP_COMMAND = [sys.executable, str(_MODULE_DIR / "slack_retrieve_mcp_server.py")]
REMOTE_MCP_NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")


def _is_present(value: str | None) -> bool:
    return bool(value and value.strip())


def _normalize_gitlab_api_url(url: str) -> str:
    normalized = url.strip().rstrip("/")
    if not normalized:
        return "https://gitlab.com/api/v4"
    if normalized.endswith("/api/v4"):
        return normalized
    if normalized == "https://gitlab.com":
        return "https://gitlab.com/api/v4"
    return f"{normalized}/api/v4" if "/api/" not in normalized else normalized


def _parse_remote_mcp_servers(raw: str) -> list[dict[str, str]]:
    if not raw.strip():
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse REMOTE_MCP_SERVERS: %s", exc)
        return []
    if not isinstance(payload, list):
        logger.warning("REMOTE_MCP_SERVERS must be a JSON array.")
        return []

    rows: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip().lower()
        url = str(item.get("url", "")).strip()
        if not name or not url:
            continue
        if not REMOTE_MCP_NAME_PATTERN.fullmatch(name):
            logger.warning("Skipping custom MCP with invalid name: %s", name)
            continue
        rows.append({
            "name": name,
            "url": url,
        })
    return rows


def _resolve_npx_binary() -> str | None:
    direct = shutil.which("npx") or shutil.which("npx.cmd")
    if direct:
        return direct

    candidates: list[Path] = []
    if _running_on_windows():
        candidates.extend([
            Path(os.environ.get("ProgramFiles", "")) / "nodejs" / "npx.cmd",
            Path(os.environ.get("ProgramFiles(x86)", "")) / "nodejs" / "npx.cmd",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "nodejs" / "npx.cmd",
            Path(os.environ.get("APPDATA", "")) / "npm" / "npx.cmd",
            Path.home() / "AppData" / "Roaming" / "npm" / "npx.cmd",
        ])
    else:
        candidates.extend([
            Path("/opt/homebrew/bin/npx"),
            Path("/usr/local/bin/npx"),
            Path.home() / ".local" / "bin" / "npx",
            Path.home() / ".npm-global" / "bin" / "npx",
        ])
        candidates.extend(sorted((Path.home() / ".nvm" / "versions" / "node").glob("*/bin/npx"), reverse=True))

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def _running_on_windows() -> bool:
    return os.name == "nt"


def _npx_command(*args: str) -> tuple[list[str], dict[str, str] | None]:
    npx_binary = _resolve_npx_binary()
    if not npx_binary:
        return ["npx", "-y", *args], None

    bin_dir = str(Path(npx_binary).parent)
    inherited_path = os.environ.get("PATH", "")
    prefixed_path = bin_dir if not inherited_path else f"{bin_dir}{os.pathsep}{inherited_path}"
    return [npx_binary, "-y", *args], {"PATH": prefixed_path}


def _merge_env(base: dict[str, str] | None, extra: dict[str, str] | None) -> dict[str, str] | None:
    if base is None and extra is None:
        return None
    merged: dict[str, str] = {}
    if extra:
        merged.update(extra)
    if base:
        merged.update(base)
    return merged


def _external_mcp_configs(settings: KiraClawSettings) -> list[McpServerConfig]:
    configs: list[McpServerConfig] = []
    npx_env: dict[str, str] | None

    if settings.perplexity_enabled and _is_present(settings.perplexity_api_key):
        command, npx_env = _npx_command("server-perplexity-ask")
        configs.append(
            McpServerConfig(
                name="perplexity",
                command=command,
                env=_merge_env({"PERPLEXITY_API_KEY": settings.perplexity_api_key}, npx_env),
                wire_format="line",
            )
        )

    if settings.gitlab_enabled and _is_present(settings.gitlab_personal_access_token):
        command, npx_env = _npx_command("@zereight/mcp-gitlab")
        configs.append(
            McpServerConfig(
                name="gitlab",
                command=command,
                env=_merge_env({
                    "GITLAB_PERSONAL_ACCESS_TOKEN": settings.gitlab_personal_access_token,
                    "GITLAB_API_URL": _normalize_gitlab_api_url(settings.gitlab_api_url),
                    "GITLAB_READ_ONLY_MODE": "false",
                    "USE_GITLAB_WIKI": "false",
                    "USE_MILESTONE": "false",
                    "USE_PIPELINE": "false",
                }, npx_env),
                wire_format="line",
            )
        )

    if settings.ms365_enabled and _is_present(settings.ms365_client_id) and _is_present(settings.ms365_tenant_id):
        command, npx_env = _npx_command("@batteryho/lokka-cached")
        configs.append(
            McpServerConfig(
                name="ms365",
                command=command,
                env=_merge_env({
                    "TENANT_ID": settings.ms365_tenant_id,
                    "CLIENT_ID": settings.ms365_client_id,
                    "USE_INTERACTIVE": "true",
                }, npx_env),
                wire_format="line",
            )
        )

    if settings.atlassian_enabled:
        resource = settings.atlassian_confluence_site_url.strip() or settings.atlassian_jira_site_url.strip()
        command, npx_env = _npx_command("mcp-remote", "https://mcp.atlassian.com/v1/sse")
        if resource:
            command.extend(["--resource", resource.rstrip("/") + "/"])
        configs.append(
            McpServerConfig(
                name="atlassian",
                command=command,
                env=npx_env,
                wire_format="line",
            )
        )

    if (
        settings.tableau_enabled
        and _is_present(settings.tableau_server)
        and _is_present(settings.tableau_site_name)
        and _is_present(settings.tableau_pat_name)
        and _is_present(settings.tableau_pat_value)
    ):
        command, npx_env = _npx_command("@tableau/mcp-server@latest")
        configs.append(
            McpServerConfig(
                name="tableau",
                command=command,
                env=_merge_env({
                    "SERVER": settings.tableau_server,
                    "SITE_NAME": settings.tableau_site_name,
                    "PAT_NAME": settings.tableau_pat_name,
                    "PAT_VALUE": settings.tableau_pat_value,
                }, npx_env),
            )
        )

    if settings.browser_enabled and settings.browser_profile_dir is not None:
        command, npx_env = _npx_command("@playwright/mcp@latest")
        command.extend(["--browser", "chrome", "--user-data-dir", str(settings.browser_profile_dir)])
        if settings.browser_output_dir is not None:
            command.extend(["--output-dir", str(settings.browser_output_dir)])
        configs.append(
            McpServerConfig(
                name="playwright",
                command=command,
                env=npx_env,
            )
        )

    for server in _parse_remote_mcp_servers(settings.remote_mcp_servers):
        command, npx_env = _npx_command("mcp-remote", server["url"])
        configs.append(
            McpServerConfig(
                name=server["name"],
                command=command,
                env=npx_env,
                wire_format="line",
            )
        )

    return configs


def _server_start_timeout(name: str) -> float:
    if name == "playwright":
        return PLAYWRIGHT_MCP_SERVER_START_TIMEOUT
    if name in {"context7", "arxiv", "youtube-info", "perplexity", "gitlab", "ms365", "atlassian", "tableau"}:
        return EXTERNAL_MCP_SERVER_START_TIMEOUT
    return DEFAULT_MCP_SERVER_START_TIMEOUT


def build_mcp_server_configs(settings: KiraClawSettings) -> list[McpServerConfig]:
    if not settings.mcp_enabled:
        return []

    configs: list[McpServerConfig] = []
    if settings.mcp_time_enabled:
        command, npx_env = _npx_command("@theo.foobar/mcp-time")
        configs.append(
            McpServerConfig(
                name="time",
                command=command,
                env=npx_env,
            )
        )
    if settings.mcp_files_enabled:
        configs.append(
            McpServerConfig(
                name="files",
                command=FILES_MCP_COMMAND,
                env={"KIRACLAW_WORKSPACE_DIR": str(settings.workspace_dir)},
            )
        )
    if settings.mcp_scheduler_enabled and settings.schedule_file is not None:
        configs.append(
            McpServerConfig(
                name="scheduler",
                command=SCHEDULER_MCP_COMMAND,
                env={
                    "KIRACLAW_SCHEDULE_FILE": str(settings.schedule_file),
                    "KIRACLAW_HOST": settings.host,
                    "KIRACLAW_PORT": str(settings.port),
                },
            )
        )
    if settings.mcp_context7_enabled:
        command, npx_env = _npx_command("@upstash/context7-mcp")
        configs.append(
            McpServerConfig(
                name="context7",
                command=command,
                env=npx_env,
                wire_format="line",
            )
        )
    if settings.mcp_arxiv_enabled:
        command, npx_env = _npx_command("@langgpt/arxiv-paper-mcp@latest")
        configs.append(
            McpServerConfig(
                name="arxiv",
                command=command,
                env=npx_env,
                wire_format="line",
            )
        )
    if settings.mcp_youtube_info_enabled:
        command, npx_env = _npx_command("@limecooler/yt-info-mcp")
        configs.append(
            McpServerConfig(
                name="youtube-info",
                command=command,
                env=npx_env,
                wire_format="line",
            )
        )
    if settings.slack_retrieve_enabled and _is_present(settings.slack_retrieve_token):
        configs.append(
            McpServerConfig(
                name="slack-retrieve",
                command=SLACK_RETRIEVE_MCP_COMMAND,
                env={
                    "KIRACLAW_SLACK_RETRIEVE_TOKEN": settings.slack_retrieve_token,
                },
            )
        )
    configs.extend(_external_mcp_configs(settings))
    return configs
class McpRuntime:
    def __init__(self, settings: KiraClawSettings) -> None:
        self.settings = settings
        self.state: str = "disabled"
        self.last_error: str | None = None
        self.failed_server_names: list[str] = []
        self._servers: list[McpServer] = []
        self.tools = []
        self.loaded_server_names: list[str] = []
        self.deferred_server_names: list[str] = []
        self._lock = threading.RLock()

    def _start_server(self, config: McpServerConfig) -> tuple[McpServer | None, str | None]:
        server = McpServer(config)
        holder: dict[str, Exception | None] = {"error": None}
        started = threading.Event()
        timeout_seconds = _server_start_timeout(config.name)

        def _target() -> None:
            try:
                server.start()
            except Exception as exc:
                holder["error"] = exc
            finally:
                started.set()

        try:
            thread = threading.Thread(
                target=_target,
                name=f"mcp-start:{config.name}",
                daemon=True,
            )
            thread.start()
            if not started.wait(timeout=timeout_seconds):
                try:
                    server.stop()
                except Exception:
                    logger.exception("Failed to stop timed out MCP server %s", config.name)
                raise TimeoutError(f"startup timed out after {timeout_seconds:.0f}s")

            if holder["error"] is not None:
                raise holder["error"]

            logger.info("MCP server started: %s (%s tools)", config.name, len(server.tools))
            return server, None
        except Exception as exc:
            logger.exception("Failed to start MCP server %s", config.name)
            return None, str(exc)

    def _refresh_state_locked(self) -> None:
        if self._servers:
            self.state = "running"
        elif self.last_error:
            self.state = "failed"
        else:
            self.state = "disabled"

    def _activate_configs(self, configs: list[McpServerConfig]) -> list[str]:
        loaded_names: list[str] = []
        failed_names: list[str] = []

        for config in configs:
            with self._lock:
                if config.name in self.loaded_server_names or config.name in self.failed_server_names:
                    continue

            if config.name in loaded_names or config.name in failed_names:
                continue

            server, error = self._start_server(config)
            if server is None:
                self.last_error = f"{config.name}: {error}"
                failed_names.append(config.name)
            else:
                with self._lock:
                    self._servers.append(server)
                    self.tools.extend(server.tools)
                    self.loaded_server_names.append(config.name)
                    loaded_names.append(config.name)

        with self._lock:
            if failed_names:
                for name in failed_names:
                    if name not in self.failed_server_names:
                        self.failed_server_names.append(name)
            self._refresh_state_locked()

        return loaded_names

    async def start(self) -> None:
        await self.stop()

        configs = build_mcp_server_configs(self.settings)
        if not configs:
            with self._lock:
                self.state = "disabled"
                self.last_error = None
                self.failed_server_names = []
            return

        with self._lock:
            self.state = "starting"
            self.last_error = None
            self.failed_server_names = []
            self.deferred_server_names = []

        self._activate_configs(configs)

    async def stop(self) -> None:
        for server in list(self._servers):
            try:
                server.stop()
            except Exception:
                logger.exception("Failed to stop MCP server %s", server.config.name)

        with self._lock:
            self._servers = []
            self.tools = []
            self.loaded_server_names = []
            self.deferred_server_names = []
            self.failed_server_names = []
            self.last_error = None
            self.state = "disabled"

    @property
    def tool_names(self) -> list[str]:
        return [tool.name for tool in self.tools]
