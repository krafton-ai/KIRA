"""
Bot Thread Context Detector Agent

스레드에서 봇이 참여 중이고, 현재 메시지가 봇에게 추가 질의인지 판단하는 에이전트
"""

import logging
import os

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)
from slack_sdk.web.async_client import AsyncWebClient

from app.config.settings import get_settings


def create_system_prompt(bot_name: str) -> str:
    """스레드 맥락 감지를 위한 system prompt 생성

    Args:
        bot_name: 봇의 이름

    Returns:
        str: 스레드 맥락 감지를 위한 system prompt
    """
    system_prompt = f"""당신은 스레드 대화를 분석하여 사용자 메시지가 다음의 대상 "{bot_name}"에게 추가 질의하는 것인지 판단하는 에이전트입니다.

## 핵심 행동 원칙
<important_actions>
1. 스레드 대화 내역에서 대상 "{bot_name}"이 이전에 답변했는지 확인합니다.
2. 대상이 참여하지 않은 스레드는 반드시 false입니다.
3. 대상이 참여했더라도, 현재 메시지가 대상과 무관한 대화라면 false입니다.
4. 다음 경우는 true로 판단합니다:
   - 대상의 답변에 대한 후속 질문 (예: "그건 뭐야?", "더 알려줘", "어떻게 해?")
   - 대상의 이전 답변을 참조 (예: "아까 말한 거", "이전에 알려준 ~")
   - 대상이 처리한 작업에 대한 추가 요청
   - 스레드 주제가 대상과 관련되고 맥락상 대상에게 묻는 것
5. 다음 경우는 false로 판단합니다:
   - 전혀 다른 주제의 새로운 질문
   - 다른 사람들끼리의 대화
   - 대상이 스레드에 참여한 적 없음
   - 일상적인 감탄/반응 (예: "오", "ㅋㅋ", "좋네")
</important_actions>

## 출력 형식
<output_format>
대상에게 추가 질의: "true" 출력
대상에게 질의 아님: "false" 출력
</output_format>"""

    return system_prompt


async def call_bot_thread_context_detector(
    thread_ts: str,
    channel_id: str,
    current_message: str,
    client: AsyncWebClient
) -> bool:
    """
    스레드에서 봇이 참여 중이고, 현재 메시지가 봇에게 추가 질의인지 판단

    Args:
        thread_ts: 스레드 타임스탬프
        channel_id: 채널 ID
        current_message: 현재 사용자 메시지
        client: Slack AsyncWebClient

    Returns:
        bool: 봇에게 추가 질의하는 것이면 True
    """
    settings = get_settings()
    bot_name = settings.BOT_NAME or "KIRA"

    try:
        # 1. 스레드 대화 내역 가져오기
        response = await client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=10  # 최근 10개 메시지
        )

        if not response.get("ok"):
            logging.warning(f"[BOT_THREAD_CONTEXT] Failed to fetch thread replies: {response.get('error')}")
            return False

        # Lazy import로 순환 import 회피
        from app.cc_slack_handlers import get_bot_user_id
        bot_user_id = get_bot_user_id()
        thread_messages = []
        bot_participated = False

        for msg in response.get("messages", []):
            user_id = msg.get("user")
            text = msg.get("text", "")

            if user_id == bot_user_id:
                thread_messages.append(f"{bot_name}: {text}")
                bot_participated = True
            else:
                # 사용자 정보 가져오기 (간단하게 user_id 사용)
                thread_messages.append(f"사용자({user_id}): {text}")

        # 봇이 참여하지 않았으면 바로 False
        if not bot_participated:
            logging.info(f"[BOT_THREAD_CONTEXT] Bot not participated in thread {thread_ts}")
            return False

        # 2. LLM에게 판단 요청
        system_prompt = create_system_prompt(bot_name)

        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            model=settings.MODEL_FOR_SIMPLE,
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

        async with ClaudeSDKClient(options=options) as sdk_client:
            conversation = "\n".join(thread_messages)
            query = f"""스레드 대화 내역:
{conversation}

현재 사용자 메시지: {current_message}

이 메시지가 대상 "{bot_name}"에게 추가 질의하는 것입니까?"""

            await sdk_client.query(query)

            async for message in sdk_client.receive_response():
                if isinstance(message, ResultMessage):
                    result_text = message.result.strip().lower()
                    logging.info(f"[BOT_THREAD_CONTEXT] Response: {result_text}")
                    return "true" in result_text

    except Exception as e:
        logging.error(f"[BOT_THREAD_CONTEXT] Error: {e}")

    return False
