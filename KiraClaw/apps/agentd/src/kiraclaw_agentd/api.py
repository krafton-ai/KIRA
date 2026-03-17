from __future__ import annotations

import asyncio
import os
import signal

from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel, Field

from kiraclaw_agentd.engine import KiraClawEngine, RunResult
from kiraclaw_agentd.memory_runtime import MemoryRuntime
from kiraclaw_agentd.scheduler_runtime import SchedulerRuntime
from kiraclaw_agentd.session_manager import SessionManager
from kiraclaw_agentd.settings import get_settings
from kiraclaw_agentd.slack_adapter import SlackGateway
from kiraclaw_agentd.watch_models import WatchSpec
from kiraclaw_agentd.watch_runtime import WatchRuntime


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


class WatchRequest(BaseModel):
    watch_id: str | None = None
    interval_minutes: int
    condition: str
    action: str
    channel_id: str | None = None
    provider: str | None = None
    model: str | None = None
    is_enabled: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)


def create_app() -> FastAPI:
    settings = get_settings()
    engine = KiraClawEngine(settings)
    memory_runtime = MemoryRuntime(settings)
    session_manager = SessionManager(
        engine,
        memory_context_provider=memory_runtime.build_context,
        on_record_complete=memory_runtime.enqueue_save,
    )
    slack_gateway = SlackGateway(session_manager, settings)
    scheduler_runtime = SchedulerRuntime(settings, session_manager, slack_gateway)
    watch_runtime = WatchRuntime(settings, session_manager)

    app = FastAPI(title="KiraClaw Agentd", version="0.1.0")
    app.state.session_manager = session_manager
    app.state.memory_runtime = memory_runtime
    app.state.slack_gateway = slack_gateway
    app.state.scheduler_runtime = scheduler_runtime
    app.state.watch_runtime = watch_runtime

    @app.on_event("startup")
    async def startup() -> None:
        await engine.start()
        await memory_runtime.start()
        await slack_gateway.start()
        await scheduler_runtime.start()
        await watch_runtime.start()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await watch_runtime.stop()
        await scheduler_runtime.stop()
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
            "memory_enabled": settings.memory_enabled,
            "watch_enabled": settings.watch_enabled,
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
            "memory_state": memory_runtime.state,
            "memory_last_error": memory_runtime.last_error,
            "memory_dir": str(settings.memory_dir) if settings.memory_dir else None,
            "memory_index_file": str(settings.memory_index_file) if settings.memory_index_file else None,
            "memory_file_count": memory_runtime.file_count,
            "memory_queue_size": memory_runtime.queued_count,
            "scheduler_state": scheduler_runtime.state,
            "scheduler_last_error": scheduler_runtime.last_error,
            "scheduler_job_count": scheduler_runtime.job_count,
            "schedule_file": str(settings.schedule_file) if settings.schedule_file else None,
            "watch_state": watch_runtime.state,
            "watch_last_error": watch_runtime.last_error,
            "watch_job_count": watch_runtime.job_count,
            "watch_file": str(settings.watch_file) if settings.watch_file else None,
            "watch_state_file": str(settings.watch_state_file) if settings.watch_state_file else None,
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

    @app.get("/v1/watches")
    async def watches() -> dict:
        return {"watches": [watch.model_dump() for watch in watch_runtime.list_watches()]}

    @app.get("/v1/watch-runs")
    async def watch_runs(limit: int = 50, watch_id: str | None = None) -> dict:
        return {
            "runs": [row.model_dump() for row in watch_runtime.list_runs(limit=limit, watch_id=watch_id)],
        }

    @app.post("/v1/watches")
    async def save_watch(request: WatchRequest) -> dict:
        spec = WatchSpec.model_validate(request.model_dump(exclude_none=True))
        try:
            saved = await watch_runtime.upsert_watch(spec)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"watch": saved.model_dump()}

    @app.delete("/v1/watches/{watch_id}")
    async def delete_watch(watch_id: str) -> dict:
        deleted = await watch_runtime.delete_watch(watch_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Unknown watch: {watch_id}")
        return {"deleted": True, "watch_id": watch_id}

    @app.post("/v1/watches/{watch_id}/run")
    async def run_watch_now(watch_id: str) -> dict:
        try:
            run = await watch_runtime.run_now(watch_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"run": run.model_dump()}

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
