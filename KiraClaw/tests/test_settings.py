from __future__ import annotations

import os
from pathlib import Path

from kiraclaw_agentd.settings import get_settings


def _write_legacy_state(home: Path, workspace: Path) -> None:
    legacy_dir = home / ".kira"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "config.env").write_text(
        "\n".join(
            [
                'SLACK_BOT_TOKEN="legacy-bot-token"',
                'SLACK_APP_TOKEN="legacy-app-token"',
                'SLACK_SIGNING_SECRET="legacy-signing-secret"',
                'SLACK_TEAM_ID="legacy-team"',
                'BOT_AUTHORIZED_USERS_EN="Jiho Jeon, Kris Choi"',
                'BOT_AUTHORIZED_USERS_KR="전지호"',
                'BOT_NAME="KIRA"',
                'OPENAI_API_KEY="legacy-openai-key"',
                'PERPLEXITY_ENABLED="true"',
                'PERPLEXITY_API_KEY="legacy-perplexity-key"',
                'GITLAB_ENABLED="true"',
                'GITLAB_API_URL="https://gitlab.com"',
                'GITLAB_PERSONAL_ACCESS_TOKEN="legacy-gitlab-token"',
                'MS365_ENABLED="true"',
                'MS365_CLIENT_ID="legacy-ms365-client"',
                'MS365_TENANT_ID="legacy-ms365-tenant"',
                'ATLASSIAN_ENABLED="true"',
                'ATLASSIAN_CONFLUENCE_SITE_URL="https://acme.atlassian.net"',
                'ATLASSIAN_JIRA_SITE_URL="https://acme.atlassian.net"',
                'ATLASSIAN_CONFLUENCE_DEFAULT_PAGE_ID="12345"',
                'TABLEAU_ENABLED="true"',
                'TABLEAU_SERVER="https://tableau.example.com"',
                'TABLEAU_SITE_NAME="craft"',
                'TABLEAU_PAT_NAME="legacy-pat-name"',
                'TABLEAU_PAT_VALUE="legacy-pat-value"',
                'REMOTE_MCP_SERVERS="[{\\"name\\":\\"docs\\",\\"url\\":\\"https://example.com/mcp\\",\\"instruction\\":\\"Use for docs\\"}]"',
                'CHROME_ENABLED="true"',
                f'FILESYSTEM_BASE_DIR="{workspace}"',
                'MODEL_FOR_COMPLEX="opus"',
            ]
        ),
        encoding="utf-8",
    )
    (legacy_dir / "credential.json").write_text("{}", encoding="utf-8")


def test_auto_mode_prefers_legacy_kira_home(tmp_path, monkeypatch) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _write_legacy_state(home, workspace)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("KIRACLAW_HOME_MODE", raising=False)
    monkeypatch.delenv("KIRACLAW_PROVIDER", raising=False)
    monkeypatch.delenv("KIRACLAW_MODEL", raising=False)
    monkeypatch.delenv("KIRACLAW_DATA_DIR", raising=False)
    monkeypatch.delenv("KIRACLAW_WORKSPACE_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.compatibility_mode is True
    assert settings.active_home_mode == "legacy"
    assert settings.data_dir == home / ".kira"
    assert settings.workspace_dir == workspace
    assert settings.provider == "vertex_ai"
    assert settings.model == "claude-opus-4-6"
    assert settings.agent_name == "KIRA"
    assert settings.skills_enabled is True
    assert settings.mcp_enabled is True
    assert settings.mcp_time_enabled is True
    assert settings.mcp_files_enabled is True
    assert settings.mcp_scheduler_enabled is True
    assert settings.mcp_context7_enabled is True
    assert settings.mcp_arxiv_enabled is True
    assert settings.mcp_youtube_info_enabled is True
    assert settings.perplexity_enabled is True
    assert settings.perplexity_api_key == "legacy-perplexity-key"
    assert settings.gitlab_enabled is True
    assert settings.gitlab_api_url == "https://gitlab.com"
    assert settings.gitlab_personal_access_token == "legacy-gitlab-token"
    assert settings.ms365_enabled is True
    assert settings.ms365_client_id == "legacy-ms365-client"
    assert settings.ms365_tenant_id == "legacy-ms365-tenant"
    assert settings.atlassian_enabled is True
    assert settings.atlassian_confluence_site_url == "https://acme.atlassian.net"
    assert settings.atlassian_jira_site_url == "https://acme.atlassian.net"
    assert settings.atlassian_confluence_default_page_id == "12345"
    assert settings.tableau_enabled is True
    assert settings.tableau_server == "https://tableau.example.com"
    assert settings.tableau_site_name == "craft"
    assert settings.tableau_pat_name == "legacy-pat-name"
    assert settings.tableau_pat_value == "legacy-pat-value"
    assert settings.remote_mcp_servers == '[{"name":"docs","url":"https://example.com/mcp","instruction":"Use for docs"}]'
    assert settings.browser_enabled is True
    assert settings.browser_profile_dir == workspace / "chrome_profile"
    assert settings.browser_output_dir == workspace / "files"
    assert settings.slack_bot_token == "legacy-bot-token"
    assert settings.slack_allowed_names == "Jiho Jeon, Kris Choi, 전지호"
    assert settings.legacy_config_loaded is True
    assert settings.active_config_file == home / ".kira" / "config.env"
    assert settings.credential_file == home / ".kira" / "credential.json"
    assert settings.schedule_file == workspace / "schedule_data" / "schedules.json"
    assert settings.watch_dir == workspace / "watch_data"
    assert settings.watch_file == workspace / "watch_data" / "watches.json"
    assert settings.watch_state_file == workspace / "watch_data" / "state.json"
    assert settings.memory_dir == workspace / "memories"
    assert settings.memory_index_file == workspace / "memories" / "index.json"
    assert os.environ["OPENAI_API_KEY"] == "legacy-openai-key"


def test_explicit_modern_home_keeps_openai_provider(tmp_path, monkeypatch) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _write_legacy_state(home, workspace)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("KIRACLAW_HOME_MODE", "modern")
    monkeypatch.setenv("KIRACLAW_PROVIDER", "openai")
    monkeypatch.delenv("KIRACLAW_MODEL", raising=False)
    monkeypatch.delenv("KIRACLAW_DATA_DIR", raising=False)
    monkeypatch.delenv("KIRACLAW_WORKSPACE_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.compatibility_mode is False
    assert settings.active_home_mode == "modern"
    assert settings.data_dir == home / ".kiraclaw"
    assert settings.workspace_dir == home / ".kiraclaw" / "workspaces" / "default"
    assert settings.provider == "openai"
    assert settings.model is None
    assert settings.agent_name == "KIRA"
    assert settings.slack_allowed_names == ""
    assert settings.skills_enabled is True
    assert settings.mcp_enabled is True
    assert settings.mcp_time_enabled is True
    assert settings.mcp_files_enabled is True
    assert settings.mcp_scheduler_enabled is True
    assert settings.mcp_context7_enabled is True
    assert settings.mcp_arxiv_enabled is True
    assert settings.mcp_youtube_info_enabled is True
    assert settings.browser_enabled is False
    assert settings.browser_profile_dir == home / ".kiraclaw" / "workspaces" / "default" / "chrome_profile"
    assert settings.browser_output_dir == home / ".kiraclaw" / "workspaces" / "default" / "files"
    assert settings.legacy_config_loaded is False
    assert settings.schedule_file == home / ".kiraclaw" / "workspaces" / "default" / "schedule_data" / "schedules.json"
    assert settings.watch_dir == home / ".kiraclaw" / "workspaces" / "default" / "watch_data"
    assert settings.watch_file == home / ".kiraclaw" / "workspaces" / "default" / "watch_data" / "watches.json"
    assert settings.watch_state_file == home / ".kiraclaw" / "workspaces" / "default" / "watch_data" / "state.json"
    assert settings.memory_dir == home / ".kiraclaw" / "workspaces" / "default" / "memories"
    assert settings.memory_index_file == home / ".kiraclaw" / "workspaces" / "default" / "memories" / "index.json"
