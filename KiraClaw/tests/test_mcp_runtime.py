from __future__ import annotations

from types import SimpleNamespace

from kiraclaw_agentd.mcp_runtime import (
    McpRuntime,
    TIME_MCP_COMMAND,
    build_mcp_server_configs,
)
from kiraclaw_agentd.settings import KiraClawSettings


def test_mcp_runtime_has_no_configs_when_disabled(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        mcp_enabled=False,
        mcp_time_enabled=True,
        mcp_files_enabled=True,
        mcp_scheduler_enabled=True,
        mcp_context7_enabled=True,
        mcp_arxiv_enabled=True,
        mcp_youtube_info_enabled=True,
    )

    configs = build_mcp_server_configs(settings)

    assert configs == []


def test_mcp_runtime_builds_time_server_config(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        mcp_enabled=True,
        mcp_time_enabled=True,
        mcp_files_enabled=False,
        mcp_scheduler_enabled=False,
        mcp_context7_enabled=False,
        mcp_arxiv_enabled=False,
        mcp_youtube_info_enabled=False,
    )

    configs = build_mcp_server_configs(settings)

    assert len(configs) == 1
    assert configs[0].name == "time"
    assert configs[0].command == TIME_MCP_COMMAND


def test_mcp_runtime_builds_files_and_scheduler_configs(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        mcp_enabled=True,
        mcp_time_enabled=False,
        mcp_files_enabled=True,
        mcp_scheduler_enabled=True,
        mcp_context7_enabled=False,
        mcp_arxiv_enabled=False,
        mcp_youtube_info_enabled=False,
    )

    configs = build_mcp_server_configs(settings)

    assert [config.name for config in configs] == ["files", "scheduler"]
    assert configs[0].env == {"KIRACLAW_WORKSPACE_DIR": str(tmp_path / "workspace")}
    assert configs[1].env == {
        "KIRACLAW_SCHEDULE_FILE": str(tmp_path / "workspace" / "schedule_data" / "schedules.json")
    }


def test_mcp_runtime_builds_remote_line_stdio_presets(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        mcp_enabled=True,
        mcp_time_enabled=False,
        mcp_files_enabled=False,
        mcp_scheduler_enabled=False,
        mcp_context7_enabled=True,
        mcp_arxiv_enabled=True,
        mcp_youtube_info_enabled=True,
    )

    configs = build_mcp_server_configs(settings)

    assert [config.name for config in configs] == ["context7", "arxiv", "youtube-info"]
    assert [config.wire_format for config in configs] == ["line", "line", "line"]


def test_mcp_runtime_builds_external_npm_configs(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        mcp_enabled=True,
        mcp_time_enabled=False,
        mcp_files_enabled=False,
        mcp_scheduler_enabled=False,
        mcp_context7_enabled=False,
        mcp_arxiv_enabled=False,
        mcp_youtube_info_enabled=False,
        perplexity_enabled=True,
        perplexity_api_key="perplexity-key",
        gitlab_enabled=True,
        gitlab_api_url="https://gitlab.com",
        gitlab_personal_access_token="gitlab-token",
        ms365_enabled=True,
        ms365_client_id="client-id",
        ms365_tenant_id="tenant-id",
        atlassian_enabled=True,
        atlassian_confluence_site_url="https://acme.atlassian.net",
        tableau_enabled=True,
        tableau_server="https://tableau.example.com",
        tableau_site_name="craft",
        tableau_pat_name="pat-name",
        tableau_pat_value="pat-value",
        remote_mcp_servers='[{"name":"docs","url":"https://example.com/mcp","instruction":"Use for docs"}]',
        browser_enabled=True,
    )

    configs = build_mcp_server_configs(settings)

    assert [config.name for config in configs] == ["perplexity", "gitlab", "ms365", "atlassian", "tableau", "playwright", "docs"]
    assert configs[0].env == {"PERPLEXITY_API_KEY": "perplexity-key"}
    assert configs[0].wire_format == "line"
    assert configs[1].env["GITLAB_API_URL"] == "https://gitlab.com/api/v4"
    assert configs[1].wire_format == "line"
    assert configs[2].env == {
        "TENANT_ID": "tenant-id",
        "CLIENT_ID": "client-id",
        "USE_INTERACTIVE": "true",
    }
    assert configs[2].wire_format == "line"
    assert configs[3].command[-2:] == ["--resource", "https://acme.atlassian.net/"]
    assert configs[4].env == {
        "SERVER": "https://tableau.example.com",
        "SITE_NAME": "craft",
        "PAT_NAME": "pat-name",
        "PAT_VALUE": "pat-value",
    }
    assert configs[5].command[:5] == ["npx", "-y", "@playwright/mcp@latest", "--browser", "chrome"]
    assert "--user-data-dir" in configs[5].command
    assert "--output-dir" in configs[5].command
    assert configs[6].command == ["npx", "-y", "mcp-remote", "https://example.com/mcp"]
    assert configs[6].wire_format == "line"


def test_mcp_runtime_includes_external_servers_for_startup(tmp_path) -> None:
    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        mcp_enabled=True,
        mcp_time_enabled=False,
        mcp_files_enabled=False,
        mcp_scheduler_enabled=False,
        mcp_context7_enabled=False,
        mcp_arxiv_enabled=False,
        mcp_youtube_info_enabled=False,
        perplexity_enabled=True,
        perplexity_api_key="perplexity-key",
        gitlab_enabled=True,
        gitlab_api_url="https://gitlab.com",
        gitlab_personal_access_token="gitlab-token",
        ms365_enabled=True,
        ms365_client_id="client-id",
        ms365_tenant_id="tenant-id",
        atlassian_enabled=True,
        atlassian_confluence_site_url="https://acme.atlassian.net",
        tableau_enabled=True,
        tableau_server="https://tableau.example.com",
        tableau_site_name="craft",
        tableau_pat_name="pat-name",
        tableau_pat_value="pat-value",
        remote_mcp_servers='[{"name":"docs","url":"https://example.com/mcp"}]',
        browser_enabled=True,
    )

    configs = build_mcp_server_configs(settings)

    assert [config.name for config in configs] == ["perplexity", "gitlab", "ms365", "atlassian", "tableau", "playwright", "docs"]


def test_mcp_runtime_start_loads_all_configs(tmp_path, monkeypatch) -> None:
    class FakeServer:
        def __init__(self, config):
            self.config = config
            self.tools = [SimpleNamespace(name=f"{config.name}_tool")]

        def start(self):
            return None

        def stop(self):
            return None

    monkeypatch.setattr("kiraclaw_agentd.mcp_runtime.McpServer", FakeServer)

    settings = KiraClawSettings(
        data_dir=tmp_path / "data",
        workspace_dir=tmp_path / "workspace",
        home_mode="modern",
        slack_enabled=False,
        mcp_enabled=True,
        mcp_time_enabled=False,
        mcp_files_enabled=False,
        mcp_scheduler_enabled=False,
        mcp_context7_enabled=False,
        mcp_arxiv_enabled=False,
        mcp_youtube_info_enabled=False,
        perplexity_enabled=True,
        perplexity_api_key="perplexity-key",
        gitlab_enabled=True,
        gitlab_api_url="https://gitlab.com",
        gitlab_personal_access_token="gitlab-token",
        ms365_enabled=True,
        ms365_client_id="client-id",
        ms365_tenant_id="tenant-id",
        atlassian_enabled=True,
        atlassian_confluence_site_url="https://acme.atlassian.net",
        remote_mcp_servers='[{"name":"docs","url":"https://example.com/mcp"}]',
        browser_enabled=True,
    )

    runtime = McpRuntime(settings)

    import asyncio

    asyncio.run(runtime.start())

    assert runtime.loaded_server_names == ["perplexity", "gitlab", "ms365", "atlassian", "playwright", "docs"]
    assert runtime.deferred_server_names == []
    assert runtime.failed_server_names == []
    assert runtime.loaded_server_names == ["perplexity", "gitlab", "ms365", "atlassian", "playwright", "docs"]
    assert runtime.tool_names == ["perplexity_tool", "gitlab_tool", "ms365_tool", "atlassian_tool", "playwright_tool", "docs_tool"]

    asyncio.run(runtime.stop())
