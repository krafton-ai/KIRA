from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field
from pydantic import model_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def derive_watch_title(condition: str, action: str = "") -> str:
    for value in (condition, action):
        text = " ".join(str(value or "").split()).strip()
        if text:
            return text[:69].rstrip() + "..." if len(text) > 72 else text
    return "Watch"


class WatchSpec(BaseModel):
    watch_id: str = Field(default_factory=lambda: str(uuid4()))
    interval_minutes: int = Field(ge=1, le=10_080)
    condition: str
    action: str
    channel_id: str | None = None
    provider: str | None = None
    model: str | None = None
    is_enabled: bool = True
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_schedule(cls, value):
        if not isinstance(value, dict):
            return value
        if value.get("interval_minutes") is not None:
            return value

        schedule_type = str(value.get("schedule_type", "")).strip()
        schedule_value = str(value.get("schedule_value", "")).strip()
        if schedule_type == "cron" and schedule_value.startswith("*/"):
            first_token = schedule_value.split()[0]
            interval_text = first_token.removeprefix("*/")
            if interval_text.isdigit():
                next_value = dict(value)
                next_value["interval_minutes"] = int(interval_text)
                return next_value
        return value

    @model_validator(mode="after")
    def _validate_required_text(self) -> "WatchSpec":
        if not self.condition.strip():
            raise ValueError("Watch condition is required.")
        if not self.action.strip():
            raise ValueError("Watch action is required.")
        return self


class WatchRunRecord(BaseModel):
    watch_run_id: str = Field(default_factory=lambda: str(uuid4()))
    watch_id: str
    watch_name: str
    session_id: str
    state: str
    summary: str = ""
    error: str | None = None
    tool_names: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    started_at: str | None = None
    finished_at: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class WatchState(BaseModel):
    runs: list[WatchRunRecord] = Field(default_factory=list)
