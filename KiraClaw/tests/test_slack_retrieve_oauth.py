from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

from kiraclaw_agentd.slack_retrieve_oauth import (
    SLACK_RETRIEVE_SCOPES,
    build_slack_retrieve_authorize_url,
    build_slack_retrieve_redirect_uri,
    update_env_file,
)


def test_build_slack_retrieve_redirect_uri() -> None:
    assert build_slack_retrieve_redirect_uri("127.0.0.1", 8787) == "http://127.0.0.1:8787/v1/oauth/slack-retrieve/callback"


def test_build_slack_retrieve_authorize_url_contains_expected_scopes() -> None:
    url = build_slack_retrieve_authorize_url(
        client_id="123.456",
        redirect_uri="http://127.0.0.1:8787/v1/oauth/slack-retrieve/callback",
        state="state-token",
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "slack.com"
    assert parsed.path == "/oauth/v2/authorize"
    assert query["client_id"] == ["123.456"]
    assert query["state"] == ["state-token"]
    assert query["redirect_uri"] == ["http://127.0.0.1:8787/v1/oauth/slack-retrieve/callback"]
    assert query["user_scope"] == [",".join(SLACK_RETRIEVE_SCOPES)]


def test_update_env_file_updates_existing_key_and_adds_missing_key(tmp_path: Path) -> None:
    target = tmp_path / "config.env"
    target.write_text('SLACK_RETRIEVE_TOKEN="old"\nOTHER_KEY="keep"\n', encoding="utf-8")

    update_env_file(target, {"SLACK_RETRIEVE_TOKEN": "new-token", "SLACK_RETRIEVE_CLIENT_ID": "123"})

    content = target.read_text(encoding="utf-8")
    assert 'SLACK_RETRIEVE_TOKEN="new-token"' in content
    assert 'OTHER_KEY="keep"' in content
    assert 'SLACK_RETRIEVE_CLIENT_ID="123"' in content
