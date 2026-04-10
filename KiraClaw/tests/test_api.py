from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from kiraclaw_agentd.api import create_app
from kiraclaw_agentd.engine import RunResult
from kiraclaw_agentd.session_manager import RunRecord
from kiraclaw_agentd.settings import get_settings
from kiraclaw_agentd.slack_retrieve_oauth import SlackRetrieveOAuthResult

_LOOPBACK_CLIENT = ("127.0.0.1", 50000)


def _disable_app_lifespan(app) -> None:
    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app.router.on_startup.clear()
    app.router.on_shutdown.clear()
    app.router.lifespan_context = _noop_lifespan


def test_runs_endpoint_returns_serializable_payload(monkeypatch) -> None:
    app = create_app()
    _disable_app_lifespan(app)

    async def fake_run(**_: object) -> SimpleNamespace:
        return SimpleNamespace(
            run_id="run-123",
            session_id="desktop:test",
            state="completed",
            result=RunResult(
                final_response="final",
                streamed_text="",
                tool_events=[],
                spoken_messages=["spoken"],
            ),
            error=None,
        )

    monkeypatch.setattr(app.state.session_manager, "run", fake_run)

    with TestClient(app, client=_LOOPBACK_CLIENT) as client:
        response = client.post(
            "/v1/runs",
            json={
                "session_id": "desktop:test",
                "prompt": "hello",
                "provider": "openai",
                "model": "gpt-5.2",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "run_id": "run-123",
        "session_id": "desktop:test",
        "state": "completed",
        "internal_summary": "final",
        "final_response": "final",
        "spoken_messages": ["spoken"],
        "streamed_text": "",
        "tool_events": [],
        "error": None,
    }


def test_slack_retrieve_oauth_flow_persists_token(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    async def fake_exchange(*, client_id: str, client_secret: str, code: str, redirect_uri: str) -> SlackRetrieveOAuthResult:
        assert client_id == "client-id"
        assert client_secret == "client-secret"
        assert code == "oauth-code"
        assert redirect_uri == "https://example.ngrok-free.dev/v1/oauth/slack-retrieve/callback"
        return SlackRetrieveOAuthResult(
            access_token="xoxp-test-token",
            scope="search:read,users:read",
            token_type="user",
            authed_user_id="U123",
        )

    monkeypatch.setattr("kiraclaw_agentd.api.exchange_slack_user_token", fake_exchange)

    with TestClient(app, client=_LOOPBACK_CLIENT) as client:
        start_response = client.post(
            "/v1/oauth/slack-retrieve/start",
            json={
                "client_id": "client-id",
                "client_secret": "client-secret",
                "redirect_uri": "https://example.ngrok-free.dev/v1/oauth/slack-retrieve/callback",
            },
        )
        assert start_response.status_code == 200
        assert start_response.json()["redirect_uri"] == "https://example.ngrok-free.dev/v1/oauth/slack-retrieve/callback"
        state = parse_qs(urlparse(start_response.json()["authorization_url"]).query)["state"][0]
        callback_response = client.get(
            "/v1/oauth/slack-retrieve/callback",
            params={"code": "oauth-code", "state": state},
        )
        status_response = client.get("/v1/oauth/slack-retrieve/status")

    assert callback_response.status_code == 200
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "success"
    assert (home / ".kira" / "config.env").read_text(encoding="utf-8").find('SLACK_RETRIEVE_TOKEN="xoxp-test-token"') != -1


def test_run_logs_endpoint_includes_live_records(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    app.state.run_log_store.observe(
        RunRecord(
            run_id="run-live",
            session_id="desktop:test",
            state="running",
            prompt="hello",
            created_at="2026-01-01T00:00:00Z",
            started_at="2026-01-01T00:00:01Z",
            result=RunResult(
                final_response="",
                streamed_text="thinking",
                tool_events=[{"phase": "start", "name": "search"}],
            ),
            metadata={"source": "api"},
        )
    )

    with TestClient(app, client=_LOOPBACK_CLIENT) as client:
        response = client.get("/v1/run-logs")

    assert response.status_code == 200
    body = response.json()
    assert body["logs"][0]["run_id"] == "run-live"
    assert body["logs"][0]["state"] == "running"
    assert body["logs"][0]["streamed_text"] == "thinking"


def test_desktop_messages_endpoint_drains_inbox(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    with TestClient(app, client=_LOOPBACK_CLIENT) as client:
        import asyncio

        asyncio.run(
            app.state.desktop_delivery.send_message(
                "desktop:local",
                "Scheduled hello",
                metadata={"source": "scheduler", "schedule_name": "Daily hello"},
            )
        )
        first = client.get("/v1/desktop-messages", params={"session_id": "desktop:local"})
        second = client.get("/v1/desktop-messages", params={"session_id": "desktop:local"})

    assert first.status_code == 200
    assert first.json()["messages"] == [
        {
            "id": first.json()["messages"][0]["id"],
            "session_id": "desktop:local",
            "text": "Scheduled hello",
            "created_at": first.json()["messages"][0]["created_at"],
            "metadata": {"source": "scheduler", "schedule_name": "Daily hello"},
        }
    ]
    assert second.status_code == 200
    assert second.json()["messages"] == []


def test_resources_endpoint_returns_gateway_and_channels(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    with TestClient(app, client=_LOOPBACK_CLIENT) as client:
        response = client.get("/v1/resources")

    assert response.status_code == 200
    body = response.json()
    resources = {(row["kind"], row["id"]): row for row in body["resources"]}
    assert ("gateway", "agentd") in resources
    assert ("channel", "slack") in resources
    assert ("channel", "telegram") in resources
    assert ("channel", "discord") in resources
    assert body["counts"]["gateway"] == 1


def test_runtime_endpoint_includes_response_trace_setting(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("KIRACLAW_RESPONSE_TRACE_ENABLED", "false")
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    with TestClient(app, client=_LOOPBACK_CLIENT) as client:
        response = client.get("/v1/runtime")

    assert response.status_code == 200
    assert response.json()["response_trace_enabled"] is False


def test_ready_endpoint_stays_200_when_optional_gateway_fails(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("KIRACLAW_SLACK_ENABLED", "true")
    monkeypatch.setenv("KIRACLAW_MCP_ENABLED", "true")
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)
    app.state.slack_gateway.state = "failed"
    app.state.engine.mcp_runtime.state = "error"

    with TestClient(app, client=_LOOPBACK_CLIENT) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["critical_checks"]["memory"] in {"idle", "ready", "not_configured", "disabled", "stopped"}
    assert body["optional_checks"]["slack"] == "failed"
    assert body["optional_checks"]["mcp"] == "error"


def test_daemon_events_endpoint_returns_resource_events(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    with TestClient(app, client=_LOOPBACK_CLIENT) as client:
        client.get("/v1/resources")
        response = client.get("/v1/daemon-events", params={"resource_kind": "gateway"})

    assert response.status_code == 200
    body = response.json()
    assert body["events"]
    assert body["events"][0]["resource_kind"] == "gateway"
    assert body["daemon_event_file"].endswith("daemon-events.jsonl")


def test_daemon_event_store_exposes_sequence_and_latest_event(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    initial_sequence = app.state.daemon_plane.events.current_sequence()
    app.state.daemon_plane.emit(
        "runtime.changed",
        message="Runtime changed",
        resource_kind="gateway",
        resource_id="agentd",
        payload={"state": "running"},
    )
    event = app.state.daemon_plane.events.wait_for_event(initial_sequence, timeout=0.01)

    assert event is not None
    assert event["type"] == "runtime.changed"
    assert event["resource_kind"] == "gateway"
    assert int(event["sequence"]) > initial_sequence


def test_desktop_delivery_waits_for_message(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    initial_sequence = app.state.desktop_delivery.current_sequence()

    import asyncio

    asyncio.run(
        app.state.desktop_delivery.send_message(
            "desktop:local",
            "hello",
            metadata={"source": "test"},
        )
    )
    sequence = app.state.desktop_delivery.wait_for_message(initial_sequence, timeout=0.01)

    assert sequence is not None
    assert int(sequence) > initial_sequence


def test_run_log_store_waits_for_update(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    initial_sequence = app.state.run_log_store.current_sequence()
    app.state.run_log_store.observe(
        RunRecord(
            run_id="run-live",
            session_id="desktop:test",
            state="running",
            prompt="hello",
            created_at="2026-01-01T00:00:00Z",
            started_at="2026-01-01T00:00:01Z",
            result=RunResult(
                final_response="",
                streamed_text="thinking",
                tool_events=[],
            ),
            metadata={"source": "api"},
        )
    )
    sequence = app.state.run_log_store.wait_for_update(initial_sequence, timeout=0.01)

    assert sequence is not None
    assert int(sequence) > initial_sequence


def test_resources_endpoint_refreshes_background_process_status(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    command = f'"{sys.executable}" -c "import time; print(\'done\'); time.sleep(0.1)"'

    with TestClient(app, client=_LOOPBACK_CLIENT) as client:
        session = app.state.engine.process_manager.start(
            command=command,
            owner_session_id="desktop:test",
        )
        time.sleep(0.2)
        response = client.get("/v1/resources")

    assert response.status_code == 200
    body = response.json()
    resources = {(row["kind"], row["id"]): row for row in body["resources"]}
    process_resource = resources[("process", session.session_id)]
    assert process_resource["state"] == "completed"


def test_v1_endpoints_reject_non_loopback_clients(monkeypatch) -> None:
    app = create_app()
    _disable_app_lifespan(app)

    with TestClient(app, client=("203.0.113.10", 50000)) as client:
        response = client.get("/v1/runtime")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "KiraClaw agentd only accepts local requests for this endpoint."
    }


def test_slack_oauth_callback_allows_non_loopback_clients(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    get_settings.cache_clear()

    app = create_app()
    _disable_app_lifespan(app)

    app.state.slack_retrieve_oauth["pending_state"] = "state-token"
    app.state.slack_retrieve_oauth["client_id"] = "client-id"
    app.state.slack_retrieve_oauth["client_secret"] = "client-secret"
    app.state.slack_retrieve_oauth["redirect_uri"] = "https://example.ngrok-free.dev/v1/oauth/slack-retrieve/callback"

    async def fake_exchange(**_: object) -> SlackRetrieveOAuthResult:
        return SlackRetrieveOAuthResult(
            access_token="xoxp-test-token",
            scope="search:read",
            token_type="user",
            authed_user_id="U123",
        )

    monkeypatch.setattr("kiraclaw_agentd.api.exchange_slack_user_token", fake_exchange)

    with TestClient(app, client=("203.0.113.10", 50000)) as client:
        response = client.get(
            "/v1/oauth/slack-retrieve/callback",
            params={"code": "oauth-code", "state": "state-token"},
        )

    assert response.status_code == 200
