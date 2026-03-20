from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
import secrets
from typing import Any
from urllib.parse import urlencode

import aiohttp


SLACK_RETRIEVE_SCOPES = [
    "search:read",
    "users:read",
    "channels:read",
    "groups:read",
    "im:read",
    "mpim:read",
    "channels:history",
    "groups:history",
    "im:history",
    "mpim:history",
]


@dataclass
class SlackRetrieveOAuthResult:
    access_token: str
    scope: str
    token_type: str
    authed_user_id: str


def build_slack_retrieve_redirect_uri(host: str, port: int) -> str:
    return f"http://{host}:{port}/v1/oauth/slack-retrieve/callback"


def resolve_slack_retrieve_redirect_uri(*, configured_url: str | None, host: str, port: int) -> str:
    candidate = str(configured_url or "").strip()
    return candidate or build_slack_retrieve_redirect_uri(host, port)


def build_slack_retrieve_authorize_url(*, client_id: str, redirect_uri: str, state: str) -> str:
    query = urlencode(
        {
            "client_id": client_id,
            "user_scope": ",".join(SLACK_RETRIEVE_SCOPES),
            "redirect_uri": redirect_uri,
            "state": state,
        }
    )
    return f"https://slack.com/oauth/v2/authorize?{query}"


def generate_oauth_state() -> str:
    return secrets.token_urlsafe(24)


def update_env_file(file_path: Path, updates: dict[str, str]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    marker = "# ============== KiraClaw =============="
    existing_text = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
    lines = existing_text.splitlines() if existing_text else []
    consumed: set[str] = set()

    def escape(value: str) -> str:
        return (
            str(value or "")
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
        )

    updated_lines: list[str] = []
    for line in lines:
        if "=" not in line:
            updated_lines.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key not in updates:
            updated_lines.append(line)
            continue
        consumed.add(key)
        updated_lines.append(f'{key}="{escape(updates[key])}"')

    pending_keys = [key for key in updates.keys() if key not in consumed]
    if pending_keys:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        if not any(line.strip() == marker for line in updated_lines):
            updated_lines.append(marker)
        for key in pending_keys:
            updated_lines.append(f'{key}="{escape(updates[key])}"')

    file_path.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")


async def exchange_slack_user_token(
    *,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> SlackRetrieveOAuthResult:
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    headers = {
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "code": code,
        "redirect_uri": redirect_uri,
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post("https://slack.com/api/oauth.v2.user.access", data=payload) as response:
            body: dict[str, Any] = await response.json()

    if not body.get("ok"):
        raise RuntimeError(str(body.get("error") or "Slack OAuth exchange failed"))

    access_token = str(body.get("access_token") or "").strip()
    if not access_token:
        raise RuntimeError("Slack OAuth exchange returned no access token")

    return SlackRetrieveOAuthResult(
        access_token=access_token,
        scope=str(body.get("scope") or ""),
        token_type=str(body.get("token_type") or "user"),
        authed_user_id=str(body.get("authed_user", {}).get("id") or ""),
    )
