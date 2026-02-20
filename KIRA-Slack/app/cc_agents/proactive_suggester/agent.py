"""
Proactive Suggester Agent

봇이 명시적으로 호출되지 않았지만 관련 메모리가 있을 때
사용자에게 도움을 제안하는 에이전트
"""

import logging
import os

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from app.cc_tools.confirm import create_confirm_mcp_server
from app.config.settings import get_settings


def create_system_prompt(state_prompt: str) -> str:
    """Proactive suggester를 위한 system prompt 생성

    Args:
        state_prompt: create_state_prompt()로 생성된 현재 상태 프롬프트

    Returns:
        str: Proactive suggester를 위한 system prompt
    """
    settings = get_settings()
    bot_name = settings.BOT_NAME or "KIRA"

    system_prompt = f"""당신은 Slack으로 커뮤니케이션 하는 가상 상주 직원 {bot_name}님 입니다.

# 기본 지침
과거 작업 처리 성공 사례를 통해 유용한 정보나 도움을 제공할 수 있는 경우, 동료들에게 먼저 도움을 제공하세요.

{state_prompt}

## 핵심 행동 원칙
<important_actions>
1. **사용자 요청이 구체적인 작업 요청일 때만** 제안을 고려합니다:
   - 구체적인 요청 예시:
     * "점심 메뉴 알려줘", "회의록 작성해줘", "코드 리뷰 해줘"
     * "이거 아시는 분?", "해주실 분?", "히스토리 아시는 분?"
     * "누가 담당자지?", "이거 어떻게 해?", "정보 있으신 분?"
     * "~에 대해 알고 계신 분?", "~관련 자료 있나요?"
   - 제안하지 않을 요청 예시:
     * 일상 대화: "안녕", "좋네", "그렇구나", "ㅋㅋ", "ㅇㅇ", "굿"
     * 추상적 질문: "어떻게 생각해?", "맞지?", "그치?"
     * 단순 감탄/반응: "와", "대박", "오", "헐"
2. 관련 메모리가 **구체적이고 유용한 경우**에만 제안합니다.
   - 관련 메모리가 없거나 추상적이거나 관련성이 낮다면 제안하지 않습니다.
3. 제안할 경우:
   - `mcp__confirm__request_confirmation` 도구를 사용하여 제안 메시지 전송합니다.
     * **channel_id**: state_data.current_message.channel_id
     * **user_id**: state_data.current_message.user_id
     * **user_name**: state_data.current_message.user_name
     * **confirm_message**: 사용자에게 보여줄 질문. 반드시 RESPONSE LANGUAGE에 맞춰 작성 (Korean: "철수님, 예전에 도와드린 적 있는데 도와드릴까요?" / English: "Hi John, I helped with this before. Would you like me to assist?")
     * **original_request_text**: 승인 시 실행할 명령. 반드시 RESPONSE LANGUAGE에 맞춰 작성 (Korean: "{bot_name}님, [사용자의 요청]" / English: "{bot_name}, [user's request]")
     * **message_ts**: state_data.current_message.message_ts (선택, 스레드 생성용)
     * **thread_ts**: state_data.current_message.thread_ts (선택)
   - 도구 호출 후 "true" 반환
4. 제안하지 않을 경우:
   - 도구를 호출하지 않고 "false" 반환
</important_actions>

# 제안 메시지 가이드
<request_confirmation_guide>
1. You MUST respond in the language specified in "RESPONSE LANGUAGE" section above.
2. 채널과 유저에 대한 답변 지침이 있으면 해당 지침에 따라 응답하세요.
3. 반드시 사용자 이름으로 시작하세요 (Korean: "철수님," / English: "Hi John,").
4. 반드시 AI 또는 봇임을 드러내는 표현을 피하세요.
5. 짧고 명확하게 작성하세요.
6. 과도한 이모지를 사용하지 마세요.
7. 스팸처럼 느껴지지 않도록 선별적으로 제안하세요.
8. 같은 내용을 반복해서 제안하지 마세요.
</request_confirmation_guide>

## 출력 형식
<output_format>
제안: `mcp__confirm__request_confirmation` 도구 호출 후 "true - [이유]"
비제안: "false - [이유]"

예: "true - 과거 성공 사례 있음" / "false - 일상 대화임"
</output_format>
"""

    return system_prompt


async def call_proactive_suggester(
    user_text: str,
    retrieved_memory: str,
    slack_data: dict,
    message_data: dict
) -> bool:
    """
    Proactive suggester 에이전트를 실행합니다.

    Args:
        user_text: 사용자 메시지
        retrieved_memory: 검색된 관련 메모리
        slack_data: Slack 컨텍스트 정보
        message_data: 메시지 정보

    Returns:
        bool: 제안을 보냈으면 True, 아니면 False
    """
    settings = get_settings()

    # 메모리가 없거나 "관련된 메모리가 없습니다"면 바로 False
    if not retrieved_memory or "관련된 메모리가 없습니다" in retrieved_memory:
        logging.info(f"[PROACTIVE_SUGGESTER] No relevant memory, skipping")
        return False

    # state_prompt 생성
    from app.cc_agents.state_prompt import create_state_prompt
    state_prompt = create_state_prompt(slack_data, message_data)

    # 메모리 추가
    state_prompt += f"\n\n## 관련 메모리\n<retrieved_memory>\n{retrieved_memory}\n</retrieved_memory>"

    system_prompt = create_system_prompt(state_prompt)

    options = ClaudeAgentOptions(
        mcp_servers={
            "confirm": create_confirm_mcp_server(),
        },
        system_prompt=system_prompt,
        model=settings.MODEL_FOR_MODERATE,
        permission_mode="bypassPermissions",
        allowed_tools=[
            "mcp__confirm__request_confirmation"
        ],
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
            query = f"""다음 메시지가 도움을 제안할 만한지 판단하세요.

메시지: {user_text}

제안할 경우: confirm 메시지 전송 후 "true"를 반환하세요.
제안하지 않을 경우: "false"를 반환하세요."""

            await client.query(query)

            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    result_text = message.result.strip().lower()
                    logging.info(f"[PROACTIVE_SUGGESTER] Response: {result_text}")
                    return "true" in result_text

    except Exception as e:
        logging.error(f"[PROACTIVE_SUGGESTER] Error: {e}")

    return False
