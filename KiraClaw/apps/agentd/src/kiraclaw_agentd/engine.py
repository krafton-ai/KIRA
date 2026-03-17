from __future__ import annotations

import os
from dataclasses import dataclass, field

from krim_sdk import Agent, AgentOptions, NullEventHandler
from krim_sdk.events import Event, EventType
from krim_sdk.models import ClaudeModel, OpenAIModel, VertexModel
from krim_sdk.skills import discover_skills
from krim_sdk.tools import BashTool, SkillTool, default_tools, default_tools_with_skills

from kiraclaw_agentd.mcp_runtime import McpRuntime
from kiraclaw_agentd.settings import KiraClawSettings
from kiraclaw_agentd.slack_tools import build_slack_tools
from kiraclaw_agentd.system_prompt import build_system_prompt


@dataclass
class RunResult:
    final_response: str
    streamed_text: str
    tool_events: list[dict] = field(default_factory=list)


class CapturingEventHandler(NullEventHandler):
    def __init__(self) -> None:
        self.stream_chunks: list[str] = []
        self.tool_events: list[dict] = []
        self.summary: str = ""
        self.model_errors: list[str] = []

    def on_stream(self, text: str) -> None:
        self.stream_chunks.append(text)

    def on_event(self, event: Event) -> None:
        if event.type == EventType.MODEL_ERROR:
            self.model_errors.append(event.data.get("error", "unknown model error"))

    def on_tool_start(self, name: str, args: dict) -> None:
        self.tool_events.append({"phase": "start", "name": name, "args": args})

    def on_tool_end(self, name: str, result: str) -> None:
        self.tool_events.append({"phase": "end", "name": name, "result": result})

    def on_submit(self, summary: str) -> None:
        self.summary = summary


def create_model(provider: str, model: str | None, max_tokens: int):
    if provider == "claude":
        return ClaudeModel(model or "claude-opus-4-6", max_tokens=max_tokens)
    if provider == "openai":
        return OpenAIModel(model or "gpt-5.3-codex", max_tokens=max_tokens)
    if provider == "vertex_ai":
        return VertexModel(model or "claude-opus-4-6", max_tokens=max_tokens)
    raise ValueError(f"unknown provider: {provider}")


def _configure_tools(settings: KiraClawSettings):
    if settings.skills_enabled:
        tools, skill_tool = default_tools_with_skills()
    else:
        tools = default_tools()
        skill_tool = None

    for tool in tools:
        if isinstance(tool, BashTool):
            tool.configure(
                deny_patterns=settings.deny_patterns,
                allow_commands=settings.allow_commands,
                ask_by_default=settings.ask_by_default,
                max_output_chars=settings.max_output_chars,
                cwd=str(settings.workspace_dir),
                default_timeout=settings.bash_timeout,
            )

    skills = discover_skills(settings.data_dir, None) if settings.skills_enabled else {}
    if isinstance(skill_tool, SkillTool):
        skill_tool.configure(skills)

    tools.extend(build_slack_tools(settings))
    return tools, list(skills.keys())


def _ensure_provider_credentials(settings: KiraClawSettings, provider: str) -> None:
    if provider == "claude" and not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "Claude provider is selected but ANTHROPIC_API_KEY is not configured. "
            "Set it in the environment or ~/.kira/config.env."
        )

    if provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OpenAI provider is selected but OPENAI_API_KEY is not configured. "
            "Set it in the environment or ~/.kira/config.env."
        )

    if provider == "vertex_ai":
        has_credential_file = settings.credential_file is not None and settings.credential_file.exists()
        has_env_credential = bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
        if not has_credential_file and not has_env_credential:
            raise RuntimeError(
                "Vertex AI provider is selected but no Google credentials are configured. "
                "Provide GOOGLE_APPLICATION_CREDENTIALS or ~/.kira/credential.json."
            )


class KiraClawEngine:
    def __init__(self, settings: KiraClawSettings) -> None:
        self.settings = settings
        self.mcp_runtime = McpRuntime(settings)

    async def start(self) -> None:
        await self.mcp_runtime.start()

    async def stop(self) -> None:
        await self.mcp_runtime.stop()

    def run(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> RunResult:
        selected_provider = provider or self.settings.provider
        selected_model = model or self.settings.model
        _ensure_provider_credentials(self.settings, selected_provider)
        tools, skill_names = _configure_tools(self.settings)
        tool_names = [tool.name for tool in tools]
        mcp_tools = list(self.mcp_runtime.tools)
        mcp_tool_names = [tool.name for tool in mcp_tools]
        handler = CapturingEventHandler()

        agent = Agent(
            model=create_model(
                selected_provider,
                selected_model,
                max_tokens=self.settings.max_tokens,
            ),
            provider=selected_provider,
            system_prompt=build_system_prompt(self.settings.agent_name, tool_names, skill_names, mcp_tool_names),
            tools=tools,
            mcp_tools=mcp_tools,
            options=AgentOptions(
                max_turns=self.settings.max_turns,
                token_limit=self.settings.token_limit,
            ),
            event_handler=handler,
        )
        agent.run(prompt)

        if agent.last_error is not None:
            raise RuntimeError(str(agent.last_error))
        if handler.model_errors:
            raise RuntimeError(handler.model_errors[-1])

        final_response = handler.summary or (agent.last_response or "")
        if not final_response and not handler.stream_chunks and not handler.tool_events:
            raise RuntimeError(
                "Agent run completed without a final response. "
                "Check provider credentials and model configuration."
            )
        return RunResult(
            final_response=final_response,
            streamed_text="".join(handler.stream_chunks),
            tool_events=handler.tool_events,
        )
