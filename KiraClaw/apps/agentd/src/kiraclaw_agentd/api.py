from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version as package_version
import json
import os
import signal
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from kiraclaw_agentd.channel_delivery import ChannelDelivery
from kiraclaw_agentd.daemon_plane import DaemonPlane
from kiraclaw_agentd.delivery_targets import DEFAULT_DESKTOP_SESSION_ID
from kiraclaw_agentd.desktop_delivery import DesktopDelivery
from kiraclaw_agentd.discord_adapter import DiscordGateway
from kiraclaw_agentd.engine import KiraClawEngine, RunResult, list_available_skills
from kiraclaw_agentd.memory_runtime import MemoryRuntime
from kiraclaw_agentd.observer_service import ObserverService
from kiraclaw_agentd.run_log_store import RunLogStore
from kiraclaw_agentd.schedule_store import read_schedules
from kiraclaw_agentd.scheduler_runtime import SchedulerRuntime
from kiraclaw_agentd.session_manager import SessionManager
from kiraclaw_agentd.settings import get_settings
from kiraclaw_agentd.slack_adapter import SlackGateway
from kiraclaw_agentd.slack_retrieve_oauth import (
    build_slack_retrieve_authorize_url,
    exchange_slack_user_token,
    generate_oauth_state,
    resolve_slack_retrieve_redirect_uri,
    update_env_file,
)
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


class SlackRetrieveOAuthStartRequest(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str | None = None


def _oauth_result(status: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, "message": message, **extra}


def _oauth_success_html(message: str) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>KiraClaw Slack Retrieve Connected</title>
    <style>
      body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background:#111; color:#fff; padding:32px; }}
      .card {{ max-width: 560px; margin: 48px auto; background:#1b1b1b; border:1px solid #333; border-radius:18px; padding:24px; }}
      h1 {{ margin-top:0; font-size: 24px; }}
      p {{ line-height:1.5; color:#d6d6d6; }}
    </style>
  </head>
  <body>
    <main class="card">
      <h1>Slack Retrieve connected</h1>
      <p>{message}</p>
      <p>You can close this tab and return to KiraClaw.</p>
    </main>
  </body>
</html>"""


def _oauth_error_html(message: str) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>KiraClaw Slack Retrieve Error</title>
    <style>
      body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background:#111; color:#fff; padding:32px; }}
      .card {{ max-width: 560px; margin: 48px auto; background:#1b1b1b; border:1px solid #333; border-radius:18px; padding:24px; }}
      h1 {{ margin-top:0; font-size: 24px; }}
      p {{ line-height:1.5; color:#d6d6d6; }}
    </style>
  </head>
  <body>
    <main class="card">
      <h1>Slack Retrieve connection failed</h1>
      <p>{message}</p>
      <p>You can close this tab and return to KiraClaw.</p>
    </main>
  </body>
</html>"""


def _agentd_version() -> str:
    try:
        return package_version("kiraclaw")
    except PackageNotFoundError:
        return "0.1.0"


def create_app() -> FastAPI:
    settings = get_settings()
    daemon_plane = DaemonPlane(settings)

    def observe_process(action: str, snapshot: dict[str, object]) -> None:
        session_id = str(snapshot.get("session_id") or "").strip()
        if not session_id:
            return
        status = str(snapshot.get("status") or "unknown").strip() or "unknown"
        if action == "cleared":
            daemon_plane.remove_resource(
                "process",
                session_id,
                event_type="process.cleared",
                message=f"Background process {session_id} cleared",
                payload=dict(snapshot),
            )
            return

        message_map = {
            "started": f"Background process {session_id} started",
            "finished": f"Background process {session_id} {status}",
        }
        daemon_plane.upsert_resource(
            "process",
            session_id,
            status,
            data=dict(snapshot),
            event_type=f"process.{action}",
            message=message_map.get(action, f"Background process {session_id} updated"),
        )

    def observe_mcp(action: str, payload: dict[str, Any]) -> None:
        if action == "runtime":
            state = str(payload.get("state") or "unknown").strip() or "unknown"
            daemon_plane.upsert_resource(
                "mcp_runtime",
                "default",
                state,
                data=dict(payload),
                event_type="mcp.runtime",
                message=f"MCP runtime -> {state}",
            )
            return
        if action == "server_loaded":
            name = str(payload.get("name") or "").strip()
            if name:
                daemon_plane.upsert_resource(
                    "mcp_server",
                    name,
                    "running",
                    data=dict(payload),
                    event_type="mcp.server_loaded",
                    message=f"MCP server {name} loaded",
                )
            return
        if action == "server_failed":
            name = str(payload.get("name") or "").strip()
            if name:
                daemon_plane.upsert_resource(
                    "mcp_server",
                    name,
                    "failed",
                    data=dict(payload),
                    event_type="mcp.server_failed",
                    message=f"MCP server {name} failed",
                    level="warning",
                )

    def observe_scheduler(action: str, payload: dict[str, Any]) -> None:
        if action == "runtime":
            state = str(payload.get("state") or "unknown").strip() or "unknown"
            daemon_plane.upsert_resource(
                "scheduler",
                "default",
                state,
                data=dict(payload),
                event_type="scheduler.runtime",
                message=f"Scheduler -> {state}",
            )
            return
        if action in {"schedule_fired", "schedule_completed"}:
            schedule_id = str(payload.get("schedule_id") or "").strip()
            if schedule_id:
                state = "running" if action == "schedule_fired" else str(payload.get("run_state") or "completed")
                daemon_plane.upsert_resource(
                    "schedule_run",
                    schedule_id,
                    state,
                    data=dict(payload),
                    event_type=f"scheduler.{action}",
                    message=f"Schedule {schedule_id} {state}",
                    level="warning" if payload.get("error") else "info",
                )
            return
        if action == "schedules_reloaded":
            daemon_plane.emit(
                "scheduler.schedules_reloaded",
                message="Scheduler schedules reloaded",
                resource_kind="scheduler",
                resource_id="default",
                payload=dict(payload),
            )

    engine = KiraClawEngine(
        settings,
        process_observer=observe_process,
        mcp_observer=observe_mcp,
    )
    memory_runtime = MemoryRuntime(settings)
    run_log_store = RunLogStore(settings)
    session_manager = SessionManager(
        engine,
        memory_context_provider=memory_runtime.build_context,
        on_record_complete=memory_runtime.enqueue_save,
        record_observer=run_log_store.observe,
    )
    observer_service = ObserverService(settings)
    slack_gateway = SlackGateway(session_manager, settings, observer_service=observer_service)
    telegram_gateway = TelegramGateway(session_manager, settings, observer_service=observer_service)
    discord_gateway = DiscordGateway(session_manager, settings, observer_service=observer_service)
    desktop_delivery = DesktopDelivery()
    channel_delivery = ChannelDelivery(
        slack_gateway=slack_gateway,
        telegram_gateway=telegram_gateway,
        discord_gateway=discord_gateway,
        desktop_delivery=desktop_delivery,
    )
    scheduler_runtime = SchedulerRuntime(
        settings,
        session_manager,
        channel_delivery,
        observer=observe_scheduler,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        daemon_plane.upsert_resource(
            "gateway",
            "agentd",
            "starting",
            data={"host": settings.host, "port": settings.port},
            event_type="gateway.starting",
            message="agentd starting",
        )
        await engine.start()
        await memory_runtime.start()
        await slack_gateway.start()
        await telegram_gateway.start()
        await discord_gateway.start()
        await scheduler_runtime.start()
        _sync_daemon_resources(gateway_state="running")
        daemon_plane.emit("gateway.started", message="agentd started", resource_kind="gateway", resource_id="agentd")
        try:
            yield
        finally:
            daemon_plane.upsert_resource(
                "gateway",
                "agentd",
                "stopping",
                data={"host": settings.host, "port": settings.port},
                event_type="gateway.stopping",
                message="agentd stopping",
            )
            await scheduler_runtime.stop()
            await discord_gateway.stop()
            await telegram_gateway.stop()
            await slack_gateway.stop()
            await memory_runtime.stop()
            await session_manager.stop()
            await engine.stop()
            _sync_daemon_resources(gateway_state="stopped")
            daemon_plane.upsert_resource(
                "gateway",
                "agentd",
                "stopped",
                data={"host": settings.host, "port": settings.port},
                event_type="gateway.stopped",
                message="agentd stopped",
            )

    app = FastAPI(title="KiraClaw Agentd", version=_agentd_version(), lifespan=lifespan)
    app.state.engine = engine
    app.state.session_manager = session_manager
    app.state.memory_runtime = memory_runtime
    app.state.slack_gateway = slack_gateway
    app.state.telegram_gateway = telegram_gateway
    app.state.discord_gateway = discord_gateway
    app.state.channel_delivery = channel_delivery
    app.state.desktop_delivery = desktop_delivery
    app.state.scheduler_runtime = scheduler_runtime
    app.state.run_log_store = run_log_store
    app.state.daemon_plane = daemon_plane
    app.state.observer_service = observer_service
    redirect_uri = resolve_slack_retrieve_redirect_uri(
        configured_url=settings.slack_retrieve_redirect_url,
        host=settings.host,
        port=settings.port,
    )
    app.state.slack_retrieve_oauth = {
        "pending_state": None,
        "client_id": "",
        "client_secret": "",
        "redirect_uri": redirect_uri,
        "result": _oauth_result("idle", "Slack Retrieve OAuth has not started yet."),
    }

    loopback_hosts = {"127.0.0.1", "::1", "localhost"}
    slack_callback_path = "/v1/oauth/slack-retrieve/callback"

    @app.middleware("http")
    async def enforce_loopback_only(request: Request, call_next):
        path = request.url.path
        if path.startswith("/v1/") and path != slack_callback_path:
            client_host = (request.client.host if request.client else "").strip().lower()
            if client_host not in loopback_hosts:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "KiraClaw agentd only accepts local requests for this endpoint."},
                )
        return await call_next(request)

    def _channel_resource_payload(name: str, gateway: Any) -> dict[str, Any]:
        payload = {
            "configured": bool(getattr(gateway, "configured", False)),
            "state": str(getattr(gateway, "state", "unknown") or "unknown"),
            "last_error": getattr(gateway, "last_error", None),
            "identity": dict(getattr(gateway, "identity", {}) or {}),
        }
        if name == "slack":
            payload["socket_mode_validated"] = bool(getattr(gateway, "socket_mode_validated", False))
        return payload

    def _sync_daemon_resources(*, gateway_state: str = "running") -> None:
        daemon_plane.upsert_resource(
            "gateway",
            "agentd",
            gateway_state,
            data={
                "host": settings.host,
                "port": settings.port,
                "provider": settings.provider,
                "model": settings.model,
            },
            event_type="gateway.runtime",
            message="agentd resource updated",
        )
        daemon_plane.upsert_resource(
            "channel",
            "slack",
            slack_gateway.state,
            data=_channel_resource_payload("slack", slack_gateway),
            event_type="channel.runtime",
            message=f"Channel slack -> {slack_gateway.state}",
        )
        daemon_plane.upsert_resource(
            "channel",
            "telegram",
            telegram_gateway.state,
            data=_channel_resource_payload("telegram", telegram_gateway),
            event_type="channel.runtime",
            message=f"Channel telegram -> {telegram_gateway.state}",
        )
        daemon_plane.upsert_resource(
            "channel",
            "discord",
            discord_gateway.state,
            data=_channel_resource_payload("discord", discord_gateway),
            event_type="channel.runtime",
            message=f"Channel discord -> {discord_gateway.state}",
        )
        daemon_plane.upsert_resource(
            "memory",
            "default",
            memory_runtime.state,
            data={
                "state": memory_runtime.state,
                "last_error": memory_runtime.last_error,
                "file_count": memory_runtime.file_count,
                "queued_count": memory_runtime.queued_count,
            },
            event_type="memory.runtime",
            message=f"Memory runtime -> {memory_runtime.state}",
        )
        active_process_ids: set[str] = set()
        for process_snapshot in engine.process_manager.list_sessions():
            process_id = str(process_snapshot.get("session_id") or "").strip()
            if not process_id:
                continue
            active_process_ids.add(process_id)
            daemon_plane.upsert_resource(
                "process",
                process_id,
                str(process_snapshot.get("status") or "unknown"),
                data=dict(process_snapshot),
                event_type="process.runtime",
                message=f"Background process {process_id} -> {process_snapshot.get('status') or 'unknown'}",
            )

        known_process_ids = {
            str(resource.get("id") or "").strip()
            for resource in daemon_plane.resources.list(kind="process")
            if str(resource.get("id") or "").strip()
        }
        for process_id in known_process_ids - active_process_ids:
            daemon_plane.remove_resource(
                "process",
                process_id,
                event_type="process.removed",
                message=f"Background process {process_id} removed",
            )

    def _runtime_payload() -> dict[str, Any]:
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
            "slack_retrieve_enabled": settings.slack_retrieve_enabled,
            "slack_retrieve_redirect_uri": resolve_slack_retrieve_redirect_uri(
                configured_url=settings.slack_retrieve_redirect_url,
                host=settings.host,
                port=settings.port,
            ),
            "primary_channel": settings.primary_channel,
            "slack_enabled": settings.slack_enabled,
            "slack_allowed_names": settings.slack_allowed_names,
            "desktop_app_enabled": settings.desktop_app_enabled,
            "browser_enabled": settings.browser_enabled,
            "browser_visible": settings.browser_visible,
            "browser_profile_dir": str(settings.browser_profile_dir) if settings.browser_profile_dir else None,
            "single_gateway_per_host": settings.single_gateway_per_host,
            "session_scope": settings.session_scope,
            "session_record_limit": settings.session_record_limit,
            "session_idle_seconds": settings.session_idle_seconds,
            "response_trace_enabled": settings.response_trace_enabled,
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
            "discord_enabled": settings.discord_enabled,
            "discord_configured": discord_gateway.configured,
            "discord_state": discord_gateway.state,
            "discord_last_error": discord_gateway.last_error,
            "discord_identity": discord_gateway.identity,
            "discord_allowed_names": settings.discord_allowed_names,
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
            "daemon_event_file": str(daemon_plane.event_log_file),
            "resource_counts": daemon_plane.resources.summary(),
            "workspace_dir": str(settings.workspace_dir),
            "data_dir": str(settings.data_dir),
            "legacy_data_dir": str(settings.legacy_data_dir),
            "legacy_data_present": settings.legacy_data_dir.exists(),
            "legacy_config_loaded": settings.legacy_config_loaded,
            "active_config_file": str(settings.active_config_file) if settings.active_config_file else None,
            "credential_file": str(settings.credential_file) if settings.credential_file else None,
        }

    @app.get("/health")
    async def health() -> dict:
        return {
            "status": "healthy",
            "service": "kiraclaw-agentd",
            "gateway_state": "running",
        }

    @app.get("/ready")
    async def ready() -> JSONResponse:
        checks = {
            "engine": "ready",
            "memory": memory_runtime.state,
            "scheduler": scheduler_runtime.state,
            "slack": slack_gateway.state,
            "telegram": telegram_gateway.state,
            "discord": discord_gateway.state,
            "mcp": engine.mcp_runtime.state,
        }
        unhealthy_states = {"failed", "error"}
        critical_checks = {
            "engine": checks["engine"],
            "memory": checks["memory"],
            "scheduler": checks["scheduler"],
        }
        optional_checks = {
            "slack": checks["slack"] if settings.slack_enabled else "disabled",
            "telegram": checks["telegram"] if settings.telegram_enabled else "disabled",
            "discord": checks["discord"] if settings.discord_enabled else "disabled",
            "mcp": checks["mcp"] if settings.mcp_enabled else "disabled",
        }
        critical_ready = not any(str(state or "").strip().lower() in unhealthy_states for state in critical_checks.values())
        optional_degraded = any(str(state or "").strip().lower() in unhealthy_states for state in optional_checks.values())
        payload = {
            "status": "degraded" if optional_degraded else "ready",
            "service": "kiraclaw-agentd",
            "checks": checks,
            "critical_checks": critical_checks,
            "optional_checks": optional_checks,
        }
        return JSONResponse(status_code=200 if critical_ready else 503, content=payload)

    @app.get("/v1/runtime")
    async def runtime() -> dict:
        _sync_daemon_resources()
        return _runtime_payload()

    @app.get("/v1/runtime/events")
    async def runtime_events() -> StreamingResponse:
        async def stream() -> Any:
            _sync_daemon_resources()
            snapshot = {
                "type": "snapshot",
                "runtime": _runtime_payload(),
            }
            yield f"event: runtime\ndata: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
            last_sequence = daemon_plane.events.current_sequence()
            while True:
                event = await asyncio.to_thread(daemon_plane.events.wait_for_event, last_sequence, 15.0)
                if event is None:
                    yield ": keepalive\n\n"
                    continue
                last_sequence = int(event.get("sequence") or last_sequence)
                payload = {
                    "type": "daemon_event",
                    "event": event,
                }
                yield f"event: runtime\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

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
        if record is None:
            raise HTTPException(status_code=500, detail="Run produced no record.")
        result: RunResult | None = record.result
        payload = {
            "run_id": record.run_id,
            "session_id": record.session_id,
            "state": record.state,
            "internal_summary": result.internal_summary if result else "",
            "final_response": result.final_response if result else "",
            "spoken_messages": list(result.spoken_messages) if result else [],
            "streamed_text": result.streamed_text if result else "",
            "tool_events": list(result.tool_events) if result else [],
            "error": record.error,
        }
        return payload

    @app.get("/v1/run-logs")
    async def run_logs(limit: int = 50, session_id: str | None = None) -> dict:
        return {
            "logs": run_log_store.tail(limit=limit, session_id=session_id),
            "run_log_file": str(run_log_store.log_file),
        }

    @app.get("/v1/run-logs/events")
    async def run_log_events() -> StreamingResponse:
        async def stream() -> Any:
            initial_sequence = run_log_store.current_sequence()
            yield f"event: runs\ndata: {json.dumps({'type': 'snapshot', 'sequence': initial_sequence}, ensure_ascii=False)}\n\n"
            last_sequence = initial_sequence
            while True:
                sequence = await asyncio.to_thread(run_log_store.wait_for_update, last_sequence, 15.0)
                if sequence is None:
                    yield ": keepalive\n\n"
                    continue
                last_sequence = int(sequence)
                payload = {"type": "run_log_update", "sequence": last_sequence}
                yield f"event: runs\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/v1/daemon-events")
    async def daemon_events(limit: int = 100, resource_kind: str | None = None, resource_id: str | None = None) -> dict:
        _sync_daemon_resources()
        return {
            "events": daemon_plane.events.tail(limit=limit, resource_kind=resource_kind, resource_id=resource_id),
            "daemon_event_file": str(daemon_plane.event_log_file),
        }

    @app.get("/v1/resources")
    async def resources(kind: str | None = None) -> dict:
        _sync_daemon_resources()
        return {
            "resources": daemon_plane.resources.list(kind=kind),
            "counts": daemon_plane.resources.summary(),
        }

    @app.get("/v1/desktop-messages")
    async def desktop_messages(session_id: str = DEFAULT_DESKTOP_SESSION_ID) -> dict:
        return {
            "messages": desktop_delivery.drain_messages(session_id),
            "session_id": session_id,
        }

    @app.get("/v1/desktop-messages/events")
    async def desktop_message_events(session_id: str = DEFAULT_DESKTOP_SESSION_ID) -> StreamingResponse:
        async def stream() -> Any:
            initial_sequence = desktop_delivery.current_sequence()
            yield f"event: desktop\ndata: {json.dumps({'type': 'snapshot', 'sequence': initial_sequence, 'session_id': session_id}, ensure_ascii=False)}\n\n"
            last_sequence = initial_sequence
            while True:
                sequence = await asyncio.to_thread(desktop_delivery.wait_for_message, last_sequence, 15.0)
                if sequence is None:
                    yield ": keepalive\n\n"
                    continue
                last_sequence = int(sequence)
                payload = {
                    "type": "desktop_message",
                    "sequence": last_sequence,
                    "session_id": session_id,
                }
                yield f"event: desktop\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/v1/oauth/slack-retrieve/status")
    async def slack_retrieve_oauth_status() -> dict:
        flow = app.state.slack_retrieve_oauth
        return {
            "redirect_uri": flow["redirect_uri"],
            **flow["result"],
        }

    @app.post("/v1/oauth/slack-retrieve/start")
    async def start_slack_retrieve_oauth(request: SlackRetrieveOAuthStartRequest) -> dict:
        client_id = request.client_id.strip()
        client_secret = request.client_secret.strip()
        if not client_id or not client_secret:
            raise HTTPException(status_code=400, detail="Slack Retrieve Client ID and Client Secret are required.")

        state_token = generate_oauth_state()
        redirect_uri = resolve_slack_retrieve_redirect_uri(
            configured_url=request.redirect_uri or settings.slack_retrieve_redirect_url,
            host=settings.host,
            port=settings.port,
        )
        app.state.slack_retrieve_oauth = {
            "pending_state": state_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "result": _oauth_result("pending", "Slack authorization started. Finish the flow in your browser."),
        }
        return {
            "authorization_url": build_slack_retrieve_authorize_url(
                client_id=client_id,
                redirect_uri=redirect_uri,
                state=state_token,
            ),
            "redirect_uri": redirect_uri,
            **app.state.slack_retrieve_oauth["result"],
        }

    @app.get("/v1/oauth/slack-retrieve/callback", response_class=HTMLResponse)
    async def slack_retrieve_oauth_callback(
        code: str | None = None,
        state: str | None = None,
        error: str | None = None,
    ) -> HTMLResponse:
        flow = app.state.slack_retrieve_oauth
        redirect_uri = str(
            flow.get("redirect_uri")
            or resolve_slack_retrieve_redirect_uri(
                configured_url=settings.slack_retrieve_redirect_url,
                host=settings.host,
                port=settings.port,
            )
        )

        if error:
            message = f"Slack returned an error: {error}"
            flow["result"] = _oauth_result("error", message)
            return HTMLResponse(_oauth_error_html(message), status_code=400)

        if not code or not state:
            message = "Slack OAuth callback is missing the authorization code or state."
            flow["result"] = _oauth_result("error", message)
            return HTMLResponse(_oauth_error_html(message), status_code=400)

        if state != flow.get("pending_state"):
            message = "Slack OAuth state mismatch. Start the connection flow again from KiraClaw."
            flow["result"] = _oauth_result("error", message)
            return HTMLResponse(_oauth_error_html(message), status_code=400)

        try:
            token = await exchange_slack_user_token(
                client_id=str(flow.get("client_id") or ""),
                client_secret=str(flow.get("client_secret") or ""),
                code=code,
                redirect_uri=redirect_uri,
            )
            update_env_file(
                settings.legacy_config_file,
                {"SLACK_RETRIEVE_TOKEN": token.access_token},
            )
            message = "Slack Retrieve token saved. Return to KiraClaw. The desktop app will restart the engine automatically."
            flow["result"] = _oauth_result(
                "success",
                message,
                authed_user_id=token.authed_user_id,
                scope=token.scope,
                token_type=token.token_type,
            )
            flow["pending_state"] = None
            return HTMLResponse(_oauth_success_html(message))
        except Exception as exc:
            message = str(exc)
            flow["result"] = _oauth_result("error", message)
            flow["pending_state"] = None
            return HTMLResponse(_oauth_error_html(message), status_code=500)

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
