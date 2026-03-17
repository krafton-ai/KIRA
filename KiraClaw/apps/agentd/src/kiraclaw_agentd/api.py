from __future__ import annotations

import asyncio
import os
import signal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from kiraclaw_agentd.proactive_models import CheckerEvent
from kiraclaw_agentd.proactive_service import ProactiveService
from kiraclaw_agentd.engine import KiraClawEngine, RunResult
from kiraclaw_agentd.scheduler_runtime import SchedulerRuntime
from kiraclaw_agentd.session_manager import SessionManager
from kiraclaw_agentd.settings import get_settings
from kiraclaw_agentd.slack_adapter import SlackGateway


class RunRequest(BaseModel):
    session_id: str = "default"
    prompt: str
    provider: str | None = None
    model: str | None = None


class RunResponse(BaseModel):
    run_id: str
    session_id: str
    state: str
    final_response: str
    streamed_text: str
    tool_events: list[dict]
    error: str | None = None


class CheckerEventRequest(BaseModel):
    source: str
    title: str
    summary: str
    suggestion_text: str
    execution_prompt: str | None = None
    channel_id: str | None = None
    user_id: str | None = None
    thread_ts: str | None = None
    dedupe_key: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


def create_app() -> FastAPI:
    settings = get_settings()
    engine = KiraClawEngine(settings)
    session_manager = SessionManager(engine)
    slack_gateway = SlackGateway(session_manager, settings)
    proactive_service = ProactiveService(settings)
    scheduler_runtime = SchedulerRuntime(settings, session_manager, slack_gateway)

    app = FastAPI(title="KiraClaw Agentd", version="0.1.0")
    app.state.session_manager = session_manager
    app.state.slack_gateway = slack_gateway
    app.state.proactive_service = proactive_service
    app.state.scheduler_runtime = scheduler_runtime

    @app.on_event("startup")
    async def startup() -> None:
        await engine.start()
        await slack_gateway.start()
        await proactive_service.start()
        await scheduler_runtime.start()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await scheduler_runtime.stop()
        await proactive_service.stop()
        await slack_gateway.stop()
        await session_manager.stop()
        await engine.stop()

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy", "service": "kiraclaw-agentd"}

    @app.get("/v1/runtime")
    async def runtime() -> dict:
        return {
            "available_providers": ["claude", "openai", "vertex_ai"],
            "provider": settings.provider,
            "model": settings.model,
            "agent_name": settings.agent_name,
            "skills_enabled": settings.skills_enabled,
            "mcp_enabled": settings.mcp_enabled,
            "mcp_time_enabled": settings.mcp_time_enabled,
            "mcp_files_enabled": settings.mcp_files_enabled,
            "mcp_scheduler_enabled": settings.mcp_scheduler_enabled,
            "mcp_context7_enabled": settings.mcp_context7_enabled,
            "mcp_arxiv_enabled": settings.mcp_arxiv_enabled,
            "mcp_youtube_info_enabled": settings.mcp_youtube_info_enabled,
            "primary_channel": settings.primary_channel,
            "slack_enabled": settings.slack_enabled,
            "slack_allowed_names": settings.slack_allowed_names,
            "desktop_app_enabled": settings.desktop_app_enabled,
            "browser_enabled": settings.browser_enabled,
            "browser_profile_dir": str(settings.browser_profile_dir) if settings.browser_profile_dir else None,
            "single_gateway_per_host": settings.single_gateway_per_host,
            "session_scope": settings.session_scope,
            "session_record_limit": settings.session_record_limit,
            "session_idle_seconds": settings.session_idle_seconds,
            "proactive_enabled": settings.proactive_enabled,
            "proactive_interval_seconds": settings.proactive_interval_seconds,
            "home_mode": settings.home_mode,
            "active_home_mode": settings.active_home_mode,
            "compatibility_mode": settings.compatibility_mode,
            "slack_configured": slack_gateway.configured,
            "slack_state": slack_gateway.state,
            "slack_last_error": slack_gateway.last_error,
            "slack_identity": slack_gateway.identity,
            "slack_socket_mode_validated": slack_gateway.socket_mode_validated,
            "mcp_state": engine.mcp_runtime.state,
            "mcp_last_error": engine.mcp_runtime.last_error,
            "mcp_loaded_servers": engine.mcp_runtime.loaded_server_names,
            "mcp_deferred_servers": engine.mcp_runtime.deferred_server_names,
            "mcp_failed_servers": engine.mcp_runtime.failed_server_names,
            "mcp_loaded_tools": engine.mcp_runtime.tool_names,
            "scheduler_state": scheduler_runtime.state,
            "scheduler_last_error": scheduler_runtime.last_error,
            "scheduler_job_count": scheduler_runtime.job_count,
            "schedule_file": str(settings.schedule_file) if settings.schedule_file else None,
            "workspace_dir": str(settings.workspace_dir),
            "data_dir": str(settings.data_dir),
            "legacy_data_dir": str(settings.legacy_data_dir),
            "legacy_data_present": settings.legacy_data_dir.exists(),
            "legacy_config_loaded": settings.legacy_config_loaded,
            "active_config_file": str(settings.active_config_file) if settings.active_config_file else None,
            "credential_file": str(settings.credential_file) if settings.credential_file else None,
            "checker_inbox_dir": str(settings.checker_inbox_dir) if settings.checker_inbox_dir else None,
            "proactive_state_file": str(settings.proactive_state_file) if settings.proactive_state_file else None,
        }

    @app.get("/v1/sessions")
    async def sessions() -> dict:
        return {"sessions": session_manager.list_sessions()}

    @app.get("/v1/proactive/suggestions")
    async def proactive_suggestions(limit: int = 50) -> dict:
        return {
            "suggestions": [record.model_dump() for record in proactive_service.list_suggestions(limit=limit)],
        }

    @app.post("/v1/checker-events")
    async def create_checker_event(request: CheckerEventRequest) -> dict:
        event = CheckerEvent.model_validate(request.model_dump())
        proactive_service.enqueue_event(event)
        processed = await proactive_service.process_now()
        matched = next((record for record in processed if record.event_id == event.event_id), None)
        return {
            "event": event.model_dump(),
            "suggestion": matched.model_dump() if matched else None,
        }

    @app.post("/v1/runs", response_model=RunResponse)
    async def run_agent(request: RunRequest) -> RunResponse:
        record = await session_manager.run(
            session_id=request.session_id,
            prompt=request.prompt,
            provider=request.provider,
            model=request.model,
            metadata={"source": "api"},
        )
        result: RunResult | None = record.result
        return RunResponse(
            run_id=record.run_id,
            session_id=record.session_id,
            state=record.state,
            final_response=result.final_response if result else "",
            streamed_text=result.streamed_text if result else "",
            tool_events=result.tool_events if result else [],
            error=record.error,
        )

    @app.post("/v1/admin/shutdown")
    async def shutdown() -> dict:
        async def _delayed_shutdown() -> None:
            await asyncio.sleep(0.15)
            os.kill(os.getpid(), signal.SIGINT)

        asyncio.create_task(_delayed_shutdown())
        return {"accepted": True, "message": "Shutdown requested."}

    return app
