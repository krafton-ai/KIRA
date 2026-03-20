from __future__ import annotations

DEFAULT_DESKTOP_SESSION_ID = "desktop:local"
DEFAULT_SCHEDULE_CHANNEL_TYPE = "slack"
SUPPORTED_DELIVERY_CHANNEL_TYPES = ("slack", "telegram", "discord", "desktop")
SUPPORTED_DELIVERY_CHANNEL_TYPE_SET = set(SUPPORTED_DELIVERY_CHANNEL_TYPES)


def normalize_delivery_channel(channel_type: str | None, channel_target: str | None) -> tuple[str, str]:
    normalized_type = str(channel_type or "").strip().lower()
    normalized_target = str(channel_target or "").strip()

    if normalized_type == "desktop" and not normalized_target:
        normalized_target = DEFAULT_DESKTOP_SESSION_ID

    if normalized_type not in SUPPORTED_DELIVERY_CHANNEL_TYPE_SET:
        normalized_type = DEFAULT_SCHEDULE_CHANNEL_TYPE if normalized_target else ""

    return normalized_type, normalized_target
