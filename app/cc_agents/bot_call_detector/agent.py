"""
봇 호출 감지 에이전트 (Bot Call Detector Agent)

이 모듈은 메시지가 봇을 직접 호출하는 것인지 판단합니다.
"""

import logging
import os

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from app.config.settings import get_settings
from app.cc_utils.language_helper import detect_language


def create_system_prompt(bot_name: str) -> str:
    """봇 호출 감지를 위한 system prompt 생성

    Args:
        bot_name: 봇의 이름

    Returns:
        str: 봇 호출 감지를 위한 system prompt
    """
    # 한글 이름인 경우만 줄임말 생성
    is_korean_name = detect_language(bot_name) == "Korean" if bot_name else False
    bot_short_name = bot_name[1:] if is_korean_name and len(bot_name) > 2 else None

    # 줄임말 설명
    short_name_desc = f' 혹은 "{bot_short_name}"' if bot_short_name else ''

    # 한글 패턴
    korean_patterns = f'"{bot_name}", "{bot_name}야", "{bot_name}아", "{bot_name}씨", "{bot_name}님"'
    if bot_short_name:
        korean_patterns += f'\n  - "{bot_short_name}", "{bot_short_name}야", "{bot_short_name}아", "{bot_short_name}씨", "{bot_short_name}님"'

    system_prompt = f"""You are an agent that determines whether the user's message is directly calling the target "{bot_name}"{short_name_desc}.

## Core Behavior Rules
<important_actions>
1. If the message calls the target by name to talk or request a task, respond with true.
2. The following patterns indicate a direct call (respond with true):
  Korean patterns:
  - {korean_patterns}
  English patterns:
  - "{bot_name}", "Hey {bot_name}", "Hi {bot_name}", "{bot_name}," (case-insensitive)
3. If the target name is mentioned but NOT directly addressed, respond with false.
4. If the target name is not present at all, respond with false.
</important_actions>

## Output Format
<output_format>
Target called: output "true"
Target not called: output "false"
</output_format>"""

    return system_prompt


async def call_bot_call_detector(
    message_text: str,
    bot_name: str = None
) -> bool:
    """
    봇 호출 감지 에이전트를 실행합니다.

    Args:
        message_text: 사용자가 보낸 메시지 텍스트
        bot_name: 봇의 이름 (기본값: settings에서 가져옴)

    Returns:
        bool: 봇이 호출되었는지 여부
    """
    settings = get_settings()
    if not bot_name:
        bot_name = settings.BOT_NAME or "KIRA"

    system_prompt = create_system_prompt(bot_name)

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model="haiku",
        permission_mode="bypassPermissions",
        allowed_tools=["*"],
        disallowed_tools=[
            "Bash(curl:*)",
            "Bash(rm:*)",
            "Bash(rm -r*)",
            "Bash(rm -rf*)",
            "Read(./.env)",
            "Read(./credential.json)",
            "WebFetch",
        ],
        setting_sources=['project'],
        cwd=os.getcwd()
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            query = f"""Determine if the following message is directly calling the target "{bot_name}".

Message: {message_text}"""

            await client.query(query)

            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    result_text = message.result.strip().lower()
                    logging.info(f"[BOT_CALL_DETECTOR] Response: {result_text}")
                    return "true" in result_text
    except Exception as e:
        logging.error(f"[BOT_CALL_DETECTOR] Error: {e}")

    return False
