from __future__ import annotations

import json
import logging
import re
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
TIME_MCP_COMMAND = ["npx", "-y", "@theo.foobar/mcp-time"]
FILES_MCP_COMMAND = [sys.executable, str(_MODULE_DIR / "files_mcp_server.py")]
SCHEDULER_MCP_COMMAND = [sys.executable, str(_MODULE_DIR / "scheduler_mcp_server.py")]
CONTEXT7_MCP_COMMAND = ["npx", "-y", "@upstash/context7-mcp"]
ARXIV_MCP_COMMAND = ["npx", "-y", "@langgpt/arxiv-paper-mcp@latest"]
YOUTUBE_INFO_MCP_COMMAND = ["npx", "-y", "@limecooler/yt-info-mcp"]
PERPLEXITY_MCP_COMMAND = ["npx", "-y", "server-perplexity-ask"]
GITLAB_MCP_COMMAND = ["npx", "-y", "@zereight/mcp-gitlab"]
MS365_MCP_COMMAND = ["npx", "-y", "@batteryho/lokka-cached"]
ATLASSIAN_MCP_COMMAND = ["npx", "-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
TABLEAU_MCP_COMMAND = ["npx", "-y", "@tableau/mcp-server@latest"]
PLAYWRIGHT_MCP_COMMAND = ["npx", "-y", "@playwright/mcp@latest"]
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


def _external_mcp_configs(settings: KiraClawSettings) -> list[McpServerConfig]:
    configs: list[McpServerConfig] = []

    if settings.perplexity_enabled and _is_present(settings.perplexity_api_key):
        configs.append(
            McpServerConfig(
                name="perplexity",
                command=PERPLEXITY_MCP_COMMAND,
                env={"PERPLEXITY_API_KEY": settings.perplexity_api_key},
                wire_format="line",
            )
        )

    if settings.gitlab_enabled and _is_present(settings.gitlab_personal_access_token):
        configs.append(
            McpServerConfig(
                name="gitlab",
                command=GITLAB_MCP_COMMAND,
                env={
                    "GITLAB_PERSONAL_ACCESS_TOKEN": settings.gitlab_personal_access_token,
                    "GITLAB_API_URL": _normalize_gitlab_api_url(settings.gitlab_api_url),
                    "GITLAB_READ_ONLY_MODE": "false",
                    "USE_GITLAB_WIKI": "false",
                    "USE_MILESTONE": "false",
                    "USE_PIPELINE": "false",
                },
                wire_format="line",
            )
        )

    if settings.ms365_enabled and _is_present(settings.ms365_client_id) and _is_present(settings.ms365_tenant_id):
        configs.append(
            McpServerConfig(
                name="ms365",
                command=MS365_MCP_COMMAND,
                env={
                    "TENANT_ID": settings.ms365_tenant_id,
                    "CLIENT_ID": settings.ms365_client_id,
                    "USE_INTERACTIVE": "true",
                },
                wire_format="line",
            )
        )

    if settings.atlassian_enabled:
        resource = settings.atlassian_confluence_site_url.strip() or settings.atlassian_jira_site_url.strip()
        command = list(ATLASSIAN_MCP_COMMAND)
        if resource:
            command.extend(["--resource", resource.rstrip("/") + "/"])
        configs.append(
            McpServerConfig(
                name="atlassian",
                command=command,
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
        configs.append(
            McpServerConfig(
                name="tableau",
                command=TABLEAU_MCP_COMMAND,
                env={
                    "SERVER": settings.tableau_server,
                    "SITE_NAME": settings.tableau_site_name,
                    "PAT_NAME": settings.tableau_pat_name,
                    "PAT_VALUE": settings.tableau_pat_value,
                },
            )
        )

    if settings.browser_enabled and settings.browser_profile_dir is not None:
        command = [
            *PLAYWRIGHT_MCP_COMMAND,
            "--browser",
            "chrome",
            "--user-data-dir",
            str(settings.browser_profile_dir),
        ]
        if settings.browser_output_dir is not None:
            command.extend(["--output-dir", str(settings.browser_output_dir)])
        configs.append(
            McpServerConfig(
                name="playwright",
                command=command,
            )
        )

    for server in _parse_remote_mcp_servers(settings.remote_mcp_servers):
        configs.append(
            McpServerConfig(
                name=server["name"],
                command=["npx", "-y", "mcp-remote", server["url"]],
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
        configs.append(
            McpServerConfig(
                name="time",
                command=TIME_MCP_COMMAND,
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
                env={"KIRACLAW_SCHEDULE_FILE": str(settings.schedule_file)},
            )
        )
    if settings.mcp_context7_enabled:
        configs.append(
            McpServerConfig(
                name="context7",
                command=CONTEXT7_MCP_COMMAND,
                wire_format="line",
            )
        )
    if settings.mcp_arxiv_enabled:
        configs.append(
            McpServerConfig(
                name="arxiv",
                command=ARXIV_MCP_COMMAND,
                wire_format="line",
            )
        )
    if settings.mcp_youtube_info_enabled:
        configs.append(
            McpServerConfig(
                name="youtube-info",
                command=YOUTUBE_INFO_MCP_COMMAND,
                wire_format="line",
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
