from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from kiraclaw_agentd.api import create_app
from kiraclaw_agentd.engine import RunResult
from kiraclaw_agentd.settings import get_settings
from kiraclaw_agentd.slack_retrieve_oauth import SlackRetrieveOAuthResult


def test_runs_endpoint_returns_serializable_payload(monkeypatch) -> None:
    app = create_app()
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()

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

    with TestClient(app) as client:
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
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()

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

    with TestClient(app) as client:
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
