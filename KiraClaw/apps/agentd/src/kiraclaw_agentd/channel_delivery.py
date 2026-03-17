from __future__ import annotations

from dataclasses import dataclass

from kiraclaw_agentd.slack_adapter import SlackGateway
from kiraclaw_agentd.telegram_adapter import TelegramGateway


@dataclass
class ChannelDelivery:
    slack_gateway: SlackGateway
    telegram_gateway: TelegramGateway

    async def send_text(self, channel_type: str | None, channel_target: str | None, text: str) -> bool:
        target = str(channel_target or "").strip()
        normalized_type = str(channel_type or "").strip().lower()
        if not target:
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

        return False
