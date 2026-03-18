from __future__ import annotations

import asyncio
import os
import signal

from fastapi import FastAPI
from pydantic import BaseModel

from kiraclaw_agentd.channel_delivery import ChannelDelivery
from kiraclaw_agentd.engine import KiraClawEngine, RunResult, list_available_skills
from kiraclaw_agentd.memory_runtime import MemoryRuntime
from kiraclaw_agentd.run_log_store import RunLogStore
from kiraclaw_agentd.schedule_store import read_schedules
from kiraclaw_agentd.scheduler_runtime import SchedulerRuntime
from kiraclaw_agentd.session_manager import SessionManager
from kiraclaw_agentd.settings import get_settings
from kiraclaw_agentd.slack_adapter import SlackGateway
from kiraclaw_agentd.telegram_adapter import TelegramGateway


class RunRequest(BaseModel):
    session_id: str = "default"
    prompt: str
    provider: str | None = None
    model: str | None = None


class RunResponse(BaseModel):
    run_id: str
    session_id: str
    state: str
    internal_summary: str
    final_response: str
    spoken_messages: list[str]
    streamed_text: str
    tool_events: list[dict]
    error: str | None = None


def create_app() -> FastAPI:
    settings = get_settings()
    engine = KiraClawEngine(settings)
    memory_runtime = MemoryRuntime(settings)
    run_log_store = RunLogStore(settings)
    session_manager = SessionManager(
        engine,
        memory_context_provider=memory_runtime.build_context,
        on_record_complete=memory_runtime.enqueue_save,
        record_observer=run_log_store.append,
    )
    slack_gateway = SlackGateway(session_manager, settings)
    telegram_gateway = TelegramGateway(session_manager, settings)
    channel_delivery = ChannelDelivery(slack_gateway=slack_gateway, telegram_gateway=telegram_gateway)
    scheduler_runtime = SchedulerRuntime(settings, session_manager, channel_delivery)

    app = FastAPI(title="KiraClaw Agentd", version="0.1.0")
    app.state.session_manager = session_manager
    app.state.memory_runtime = memory_runtime
    app.state.slack_gateway = slack_gateway
    app.state.telegram_gateway = telegram_gateway
    app.state.channel_delivery = channel_delivery
    app.state.scheduler_runtime = scheduler_runtime
    app.state.run_log_store = run_log_store

    @app.on_event("startup")
    async def startup() -> None:
        await engine.start()
        await memory_runtime.start()
        await slack_gateway.start()
        await telegram_gateway.start()
        await scheduler_runtime.start()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await scheduler_runtime.stop()
        await telegram_gateway.stop()
        await slack_gateway.stop()
        await memory_runtime.stop()
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
            "agent_persona": settings.agent_persona,
            "skills_enabled": settings.skills_enabled,
            "skill_count": len(list_available_skills(settings)),
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
            "memory_enabled": settings.memory_enabled,
            "home_mode": settings.home_mode,
            "active_home_mode": settings.active_home_mode,
            "compatibility_mode": settings.compatibility_mode,
            "slack_configured": slack_gateway.configured,
            "slack_state": slack_gateway.state,
            "slack_last_error": slack_gateway.last_error,
            "slack_identity": slack_gateway.identity,
            "slack_socket_mode_validated": slack_gateway.socket_mode_validated,
            "telegram_enabled": settings.telegram_enabled,
            "telegram_configured": telegram_gateway.configured,
            "telegram_state": telegram_gateway.state,
            "telegram_last_error": telegram_gateway.last_error,
            "telegram_identity": telegram_gateway.identity,
            "telegram_allowed_names": settings.telegram_allowed_names,
            "mcp_state": engine.mcp_runtime.state,
            "mcp_last_error": engine.mcp_runtime.last_error,
            "mcp_loaded_servers": engine.mcp_runtime.loaded_server_names,
            "mcp_deferred_servers": engine.mcp_runtime.deferred_server_names,
            "mcp_failed_servers": engine.mcp_runtime.failed_server_names,
            "mcp_loaded_tools": engine.mcp_runtime.tool_names,
            "memory_state": memory_runtime.state,
            "memory_last_error": memory_runtime.last_error,
            "memory_dir": str(settings.memory_dir) if settings.memory_dir else None,
            "memory_index_file": str(settings.memory_index_file) if settings.memory_index_file else None,
            "run_log_file": str(settings.run_log_file) if settings.run_log_file else None,
            "memory_file_count": memory_runtime.file_count,
            "memory_queue_size": memory_runtime.queued_count,
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
        }

    @app.get("/v1/sessions")
    async def sessions() -> dict:
        return {"sessions": session_manager.list_sessions()}

    @app.get("/v1/schedules")
    async def schedules() -> dict:
        rows = read_schedules(settings.schedule_file) if settings.schedule_file else []
        return {
            "schedules": rows,
            "schedule_file": str(settings.schedule_file) if settings.schedule_file else None,
        }

    @app.get("/v1/skills")
    async def skills() -> dict:
        return {
            "skills": list_available_skills(settings),
            "workspace_skill_dir": str(settings.workspace_dir / "skills"),
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
            internal_summary=result.internal_summary if result else "",
            final_response=result.final_response if result else "",
            spoken_messages=result.spoken_messages if result else [],
            streamed_text=result.streamed_text if result else "",
            tool_events=result.tool_events if result else [],
            error=record.error,
        )

    @app.get("/v1/run-logs")
    async def run_logs(limit: int = 50, session_id: str | None = None) -> dict:
        return {
            "logs": run_log_store.tail(limit=limit, session_id=session_id),
            "run_log_file": str(run_log_store.log_file),
        }

    @app.post("/v1/admin/shutdown")
    async def shutdown() -> dict:
        async def _delayed_shutdown() -> None:
            await asyncio.sleep(0.15)
            os.kill(os.getpid(), signal.SIGINT)

        asyncio.create_task(_delayed_shutdown())
        return {"accepted": True, "message": "Shutdown requested."}

    @app.post("/v1/admin/reload-schedules")
    async def reload_schedules() -> dict:
        await scheduler_runtime.reload_from_file(force=True)
        return {
            "accepted": True,
            "state": scheduler_runtime.state,
            "job_count": scheduler_runtime.job_count,
            "last_error": scheduler_runtime.last_error,
        }

    return app
