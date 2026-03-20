from __future__ import annotations

from dataclasses import dataclass

from kiraclaw_agentd.delivery_targets import DEFAULT_DESKTOP_SESSION_ID
from kiraclaw_agentd.desktop_delivery import DesktopDelivery
from kiraclaw_agentd.discord_adapter import DiscordGateway
from kiraclaw_agentd.slack_adapter import SlackGateway
from kiraclaw_agentd.telegram_adapter import TelegramGateway


@dataclass
class ChannelDelivery:
    slack_gateway: SlackGateway
    telegram_gateway: TelegramGateway
    discord_gateway: DiscordGateway | None = None
    desktop_delivery: DesktopDelivery | None = None

    async def send_text(
        self,
        channel_type: str | None,
        channel_target: str | None,
        text: str,
        metadata: dict | None = None,
    ) -> bool:
        target = str(channel_target or "").strip()
        normalized_type = str(channel_type or "").strip().lower()
        if not target and normalized_type != "desktop":
            return False

        if normalized_type in {"", "slack"}:
            if not self.slack_gateway.configured:
                return False
            await self.slack_gateway.send_message(target, text)
            return True

        if normalized_type == "telegram":
            if not self.telegram_gateway.configured:
                return False
            await self.telegram_gateway.send_message(target, text)
            return True

        if normalized_type == "discord":
            if self.discord_gateway is None or not self.discord_gateway.configured:
                return False
            await self.discord_gateway.send_message(target, text)
            return True

        if normalized_type == "desktop":
            if self.desktop_delivery is None:
                return False
            await self.desktop_delivery.send_message(target or DEFAULT_DESKTOP_SESSION_ID, text, metadata=metadata)
            return True

        return False
