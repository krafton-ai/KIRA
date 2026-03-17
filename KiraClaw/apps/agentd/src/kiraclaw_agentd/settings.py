from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_LEGACY_MODEL_ALIASES = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
}

_LEGACY_ENV_BACKFILL_KEYS = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "VERTEXAI_LOCATION",
    "ANTHROPIC_VERTEX_PROJECT_ID",
    "ANTHROPIC_VERTEX_REGION",
    "CLAUDE_CODE_USE_VERTEX",
]


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        cleaned = value.strip()
        if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
            cleaned = cleaned[1:-1]
        cleaned = cleaned.replace("\\\\", "\\")
        cleaned = cleaned.replace('\\"', '"')
        cleaned = cleaned.replace("\\'", "'")
        cleaned = cleaned.replace("\\n", "\n")
        values[key.strip()] = cleaned
    return values


def _map_legacy_model(name: str | None) -> str | None:
    if not name:
        return None
    return _LEGACY_MODEL_ALIASES.get(name.strip().lower(), name.strip())


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return None


class KiraClawSettings(BaseSettings):
    """Product-level settings for the local daemon."""

    model_config = SettingsConfigDict(
        env_prefix="KIRACLAW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8787

    provider: str = "claude"
    model: str | None = None
    agent_name: str = "KIRA"
    skills_enabled: bool = True
    mcp_enabled: bool = True
    mcp_time_enabled: bool = True
    mcp_files_enabled: bool = True
    mcp_scheduler_enabled: bool = True
    mcp_context7_enabled: bool = True
    mcp_arxiv_enabled: bool = True
    mcp_youtube_info_enabled: bool = True
    perplexity_enabled: bool = False
    perplexity_api_key: str = ""
    gitlab_enabled: bool = False
    gitlab_api_url: str = ""
    gitlab_personal_access_token: str = ""
    ms365_enabled: bool = False
    ms365_client_id: str = ""
    ms365_tenant_id: str = ""
    atlassian_enabled: bool = False
    atlassian_confluence_site_url: str = ""
    atlassian_confluence_default_page_id: str = ""
    atlassian_jira_site_url: str = ""
    tableau_enabled: bool = False
    tableau_server: str = ""
    tableau_site_name: str = ""
    tableau_pat_name: str = ""
    tableau_pat_value: str = ""
    browser_enabled: bool = False
    remote_mcp_servers: str = ""
    browser_profile_dir: Path | None = None
    browser_output_dir: Path | None = None
    max_turns: int = 64
    max_tokens: int = 16_384
    token_limit: int = 180_000
    max_output_chars: int = 30_000
    bash_timeout: int = 900
    ask_by_default: bool = False

    primary_channel: str = "slack"
    slack_enabled: bool = True
    slack_bot_token: str = ""
    slack_app_token: str = ""
    slack_signing_secret: str = ""
    slack_team_id: str = ""
    slack_allowed_names: str = ""
    desktop_app_enabled: bool = True
    single_gateway_per_host: bool = True
    session_scope: str = "session-lane"
    session_record_limit: int = 100
    session_idle_seconds: float = 900
    memory_enabled: bool = True
    watch_enabled: bool = True
    watch_history_limit: int = 200

    home_mode: str = "auto"
    compatibility_mode: bool = False
    active_home_mode: str = "modern"
    modern_data_dir: Path = Field(default_factory=lambda: Path.home() / ".kiraclaw")
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".kiraclaw")
    workspace_dir: Path = Field(default_factory=lambda: Path.home() / ".kiraclaw" / "workspaces" / "default")
    legacy_data_dir: Path = Field(default_factory=lambda: Path.home() / ".kira")
    legacy_config_file: Path = Field(default_factory=lambda: Path.home() / ".kira" / "config.env")
    active_config_file: Path | None = None
    credential_file: Path | None = None
    legacy_config_loaded: bool = False
    schedule_dir: Path | None = None
    schedule_file: Path | None = None
    watch_dir: Path | None = None
    watch_file: Path | None = None
    watch_state_file: Path | None = None
    memory_dir: Path | None = None
    memory_index_file: Path | None = None

    allow_commands: list[str] = Field(default_factory=lambda: [
        "ls", "cat", "head", "tail", "find", "grep", "rg", "wc",
        "git status", "git diff", "git log", "git branch",
        "python -m py_compile", "python -c",
        "npm run lint", "npm test", "pytest", "make",
    ])
    deny_patterns: list[str] = Field(default_factory=lambda: [
        "rm -rf /", "rm -rf ~", "rm -rf /*",
        "> /dev/sda", "mkfs.", "dd if=",
        ":(){:|:&};:", "chmod -R 777 /",
        "curl|sh", "curl|bash", "wget|sh", "wget|bash",
    ])

    def model_post_init(self, __context) -> None:
        explicit_fields = self.model_fields_set
        selected_data_dir = self._resolve_data_dir(explicit_fields)
        object.__setattr__(self, "data_dir", selected_data_dir)

        compatibility_mode = selected_data_dir == self.legacy_data_dir
        object.__setattr__(self, "compatibility_mode", compatibility_mode)
        object.__setattr__(self, "active_home_mode", "legacy" if compatibility_mode else "modern")

        legacy_values = _parse_env_file(self.legacy_config_file) if compatibility_mode else {}
        object.__setattr__(self, "legacy_config_loaded", bool(legacy_values))
        object.__setattr__(self, "active_config_file", self.legacy_config_file if legacy_values else None)

        credential_file = self._resolve_credential_file()
        if "credential_file" not in explicit_fields:
            object.__setattr__(self, "credential_file", credential_file)
        if self.credential_file and "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(self.credential_file)

        if compatibility_mode:
            self._apply_legacy_backfill(legacy_values, explicit_fields)

        if "workspace_dir" not in explicit_fields and not compatibility_mode:
            object.__setattr__(self, "workspace_dir", self.data_dir / "workspaces" / "default")
        if "schedule_dir" not in explicit_fields:
            object.__setattr__(self, "schedule_dir", self.workspace_dir / "schedule_data")
        if "schedule_file" not in explicit_fields:
            schedule_dir = self.schedule_dir or (self.workspace_dir / "schedule_data")
            object.__setattr__(self, "schedule_file", schedule_dir / "schedules.json")
        if "watch_dir" not in explicit_fields:
            object.__setattr__(self, "watch_dir", self.workspace_dir / "watch_data")
        if "watch_file" not in explicit_fields:
            watch_dir = self.watch_dir or (self.workspace_dir / "watch_data")
            object.__setattr__(self, "watch_file", watch_dir / "watches.json")
        if "watch_state_file" not in explicit_fields:
            watch_dir = self.watch_dir or (self.workspace_dir / "watch_data")
            object.__setattr__(self, "watch_state_file", watch_dir / "state.json")
        if "memory_dir" not in explicit_fields:
            object.__setattr__(self, "memory_dir", self.workspace_dir / "memories")
        if "memory_index_file" not in explicit_fields:
            memory_dir = self.memory_dir or (self.workspace_dir / "memories")
            object.__setattr__(self, "memory_index_file", memory_dir / "index.json")
        if "browser_profile_dir" not in explicit_fields:
            object.__setattr__(self, "browser_profile_dir", self.workspace_dir / "chrome_profile")
        if "browser_output_dir" not in explicit_fields:
            object.__setattr__(self, "browser_output_dir", self.workspace_dir / "files")

    def _resolve_data_dir(self, explicit_fields: set[str]) -> Path:
        if "data_dir" in explicit_fields:
            return self.data_dir

        if self.home_mode == "legacy":
            return self.legacy_data_dir
        if self.home_mode == "modern":
            return self.modern_data_dir
        if self.legacy_data_dir.exists():
            return self.legacy_data_dir
        return self.modern_data_dir

    def _resolve_credential_file(self) -> Path | None:
        candidates = [
            self.data_dir / "credential.json",
            self.legacy_data_dir / "credential.json",
        ]
        seen: set[Path] = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate.exists():
                return candidate
        return None

    def _apply_legacy_backfill(self, legacy_values: dict[str, str], explicit_fields: set[str]) -> None:
        for env_key in _LEGACY_ENV_BACKFILL_KEYS:
            if env_key not in os.environ and legacy_values.get(env_key):
                os.environ[env_key] = legacy_values[env_key]

        if "provider" not in explicit_fields and legacy_values.get("KIRACLAW_PROVIDER"):
            object.__setattr__(self, "provider", legacy_values["KIRACLAW_PROVIDER"].strip())

        if "agent_name" not in explicit_fields:
            if legacy_values.get("KIRACLAW_AGENT_NAME"):
                object.__setattr__(self, "agent_name", legacy_values["KIRACLAW_AGENT_NAME"].strip())
            elif legacy_values.get("BOT_NAME"):
                object.__setattr__(self, "agent_name", legacy_values["BOT_NAME"].strip())

        if "slack_allowed_names" not in explicit_fields and not self.slack_allowed_names:
            merged_allowed_names: list[str] = []
            if legacy_values.get("SLACK_ALLOWED_NAMES"):
                merged_allowed_names.extend(
                    part.strip() for part in legacy_values["SLACK_ALLOWED_NAMES"].split(",") if part.strip()
                )
            else:
                for legacy_key in ("BOT_AUTHORIZED_USERS_EN", "BOT_AUTHORIZED_USERS_KR"):
                    if legacy_values.get(legacy_key):
                        merged_allowed_names.extend(
                            part.strip() for part in legacy_values[legacy_key].split(",") if part.strip()
                        )
            if merged_allowed_names:
                deduped: list[str] = []
                seen: set[str] = set()
                for name in merged_allowed_names:
                    lowered = name.lower()
                    if lowered in seen:
                        continue
                    seen.add(lowered)
                    deduped.append(name)
                object.__setattr__(self, "slack_allowed_names", ", ".join(deduped))

        if "model" not in explicit_fields and not self.model:
            if legacy_values.get("KIRACLAW_MODEL"):
                object.__setattr__(self, "model", legacy_values["KIRACLAW_MODEL"].strip())
            else:
                object.__setattr__(self, "model", _map_legacy_model(legacy_values.get("MODEL_FOR_COMPLEX")))

        legacy_bool_field_map = {
            "skills_enabled": "KIRACLAW_SKILLS_ENABLED",
            "mcp_enabled": "KIRACLAW_MCP_ENABLED",
            "mcp_time_enabled": "KIRACLAW_MCP_TIME_ENABLED",
            "mcp_files_enabled": "KIRACLAW_MCP_FILES_ENABLED",
            "mcp_scheduler_enabled": "KIRACLAW_MCP_SCHEDULER_ENABLED",
            "mcp_context7_enabled": "KIRACLAW_MCP_CONTEXT7_ENABLED",
            "mcp_arxiv_enabled": "KIRACLAW_MCP_ARXIV_ENABLED",
            "mcp_youtube_info_enabled": "KIRACLAW_MCP_YOUTUBE_INFO_ENABLED",
            "perplexity_enabled": "PERPLEXITY_ENABLED",
            "gitlab_enabled": "GITLAB_ENABLED",
            "ms365_enabled": "MS365_ENABLED",
            "atlassian_enabled": "ATLASSIAN_ENABLED",
            "tableau_enabled": "TABLEAU_ENABLED",
            "browser_enabled": "CHROME_ENABLED",
        }
        for field_name, legacy_key in legacy_bool_field_map.items():
            if field_name in explicit_fields:
                continue
            parsed = _parse_bool(legacy_values.get(legacy_key))
            if parsed is not None:
                object.__setattr__(self, field_name, parsed)

        legacy_field_map = {
            "slack_bot_token": "SLACK_BOT_TOKEN",
            "slack_app_token": "SLACK_APP_TOKEN",
            "slack_signing_secret": "SLACK_SIGNING_SECRET",
            "slack_team_id": "SLACK_TEAM_ID",
            "perplexity_api_key": "PERPLEXITY_API_KEY",
            "gitlab_api_url": "GITLAB_API_URL",
            "gitlab_personal_access_token": "GITLAB_PERSONAL_ACCESS_TOKEN",
            "ms365_client_id": "MS365_CLIENT_ID",
            "ms365_tenant_id": "MS365_TENANT_ID",
            "atlassian_confluence_site_url": "ATLASSIAN_CONFLUENCE_SITE_URL",
            "atlassian_confluence_default_page_id": "ATLASSIAN_CONFLUENCE_DEFAULT_PAGE_ID",
            "atlassian_jira_site_url": "ATLASSIAN_JIRA_SITE_URL",
            "tableau_server": "TABLEAU_SERVER",
            "tableau_site_name": "TABLEAU_SITE_NAME",
            "tableau_pat_name": "TABLEAU_PAT_NAME",
            "tableau_pat_value": "TABLEAU_PAT_VALUE",
            "remote_mcp_servers": "REMOTE_MCP_SERVERS",
            "browser_profile_dir": "CHROME_PROFILE_DIR",
        }
        for field_name, legacy_key in legacy_field_map.items():
            current_value = getattr(self, field_name)
            if field_name not in explicit_fields and not current_value:
                object.__setattr__(self, field_name, legacy_values.get(legacy_key, ""))

        if "remote_mcp_servers" not in explicit_fields and self.remote_mcp_servers:
            try:
                json.loads(self.remote_mcp_servers)
            except json.JSONDecodeError:
                object.__setattr__(self, "remote_mcp_servers", "")

        if "workspace_dir" not in explicit_fields:
            filesystem_base_dir = legacy_values.get("FILESYSTEM_BASE_DIR", "").strip()
            if filesystem_base_dir:
                object.__setattr__(self, "workspace_dir", Path(filesystem_base_dir).expanduser())
            else:
                object.__setattr__(self, "workspace_dir", self.data_dir / "workspaces" / "default")

        if "provider" not in explicit_fields and not legacy_values.get("KIRACLAW_PROVIDER") and self.credential_file:
            object.__setattr__(self, "provider", "vertex_ai")

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "skills").mkdir(parents=True, exist_ok=True)
        (self.workspace_dir / ".krim" / "skills").mkdir(parents=True, exist_ok=True)
        if self.watch_dir:
            self.watch_dir.mkdir(parents=True, exist_ok=True)
        if self.watch_state_file:
            self.watch_state_file.parent.mkdir(parents=True, exist_ok=True)
        if self.memory_dir:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
        if self.browser_profile_dir:
            self.browser_profile_dir.mkdir(parents=True, exist_ok=True)
        if self.browser_output_dir:
            self.browser_output_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> KiraClawSettings:
    settings = KiraClawSettings()
    settings.ensure_directories()
    return settings
