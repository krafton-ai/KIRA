"""
응답 취합 에이전트 (Answer Aggregator Agent)

이 모듈은 사용자가 응답 대기 중인 질의에 답변했는지 확인하고,
모든 답변이 완료되면 취합하여 원 요청자에게 Slack 메시지로 전송합니다.
"""

import json
import logging
import os

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from app.cc_tools.waiting_answer.waiting_answer_tools import create_waiting_answer_mcp_server
from app.cc_tools.slack.slack_tools import create_slack_mcp_server
from app.cc_utils.waiting_answer_db import get_user_pending_requests
from app.config.settings import get_settings


def create_system_prompt() -> str:
    """Answer aggregator를 위한 system prompt 생성

    Returns:
        str: 답변 처리 및 취합을 위한 system prompt
    """
    system_prompt = """You are an agent that determines if a user's message is a response to a pending query and processes it accordingly.

## 핵심 행동 원칙
<important_actions>
관련 없음: 사용자 메시지가 어떤 대기 중인 질의와도 관련 없으면 false만 출력

관련 있음: 사용자 메시지가 특정 질의에 대한 답변이면 순서대로 처리
  1. `mcp__waiting_answer__update_request`로 응답 업데이트
  2. `mcp__slack__answer_with_emoji`로 사용자 메시지에 이모지 추가
  3. `mcp__waiting_answer__update_request` 결과에서 all_completed 확인
  4. all_completed가 true일 때만:
     a. `mcp__waiting_answer__update_request` 결과에서 requester_id 확인 (원 질의자 ID)
     b. `mcp__slack__get_dm_channel_id`로 requester_id의 DM 채널 ID 가져오기
     c. all_responses의 모든 답변을 취합하여 보기 좋게 정리
     d. `mcp__slack__forward_message`로 원 질의자에게 전송 (request_answer=False, channel_id는 b에서 가져온 DM 채널 ID)
</important_actions>

## 원 질의자에게 전송 메세지 가이드
<slack_forward_message_guide>
1. You MUST respond in the same language as the original query (request_content).
2. 반드시 AI 또는 봇임을 드러내는 표현을 피하세요.
3. 요청과 관련 없는 내용은 응답에 포함하지 마세요.
4. 과도한 이모지를 사용하지 마세요.
5. 반드시 시스템 관련 용어를 자연스러운 일상 표현으로 바꿔 사용하세요. (예: "메모리" → "기억/예전에 들은 거", "파일 경로" → "위치/폴더", "스레드" → "대화", "API 호출" → "확인해봤는데", "버그/에러" → "문제", "디버깅" → "확인 중", "트리거" → "실행")
6. 마크다운 문법(**, ##, -, >, ``` 등)을 사용하지 마세요. 대신 줄바꿈과 들여쓰기로 구조화하세요.
</slack_forward_message_guide>

## 가드레일 정책
<guardrails>
**엄격한 정책:**
- all_completed가 false면 `mcp__slack__forward_message` 호출 절대 금지
- `mcp__slack__forward_message` 호출 시 반드시 requester_id의 DM 채널로 전송 (응답자가 아닌 원 질의자에게)
</guardrails>

## 출력 형식
<output_format>
관련 있으면: 모든 작업 완료 후, "true" 출력
관련 없으면: "false" 출력
</output_format>"""

    return system_prompt


async def call_answer_aggregator(
    user_text: str,
    message_data: dict
) -> bool:
    """
    사용자가 응답 대기 중인 질의에 답변했는지 확인하고 처리합니다.

    Args:
        user_text: 사용자가 보낸 메시지 텍스트
        message_data: 메시지 정보 (user_id, channel_id, thread_ts 등)

    Returns:
        bool: 응답 완료 처리를 했으면 True, 아니면 False
    """
    user_id = message_data["user_id"]

    # 1. 이 사용자의 응답 대기 중인 질의 확인
    pending_requests = get_user_pending_requests(user_id)

    if not pending_requests:
        return False  # 응답 대기 중인 질의 없음

    logging.info(f"[ANSWER_AGGREGATOR] User {user_id} has {len(pending_requests)} pending request(s)")

    # 2. LLM에게 판단 요청
    system_prompt = create_system_prompt()
    settings = get_settings()

    options = ClaudeAgentOptions(
        mcp_servers={
            "waiting_answer": create_waiting_answer_mcp_server(),
            "slack": create_slack_mcp_server(),
        },
        system_prompt=system_prompt,
        model=settings.MODEL_FOR_MODERATE,
        permission_mode="bypassPermissions",
        allowed_tools=[
            "mcp__waiting_answer__update_request",
            "mcp__slack__answer_with_emoji",
            "mcp__slack__get_dm_channel_id",
            "mcp__slack__forward_message"
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
            query = f"""
다음 정보를 분석하여 처리하세요:

응답 대기 중인 질의 목록:
{json.dumps(pending_requests, ensure_ascii=False, indent=2)}

사용자 답변:
{user_text}

사용자 메시지 정보:
- channel_id: {message_data.get('channel_id')}
- message_ts: {message_data.get('message_ts')}
- user_id: {message_data.get('user_id')}
"""
            await client.query(query)

            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    result_text = message.result.strip().lower()
                    logging.info(f"[ANSWER_AGGREGATOR] Response: {result_text}")
                    return "true" in result_text
    except Exception as e:
        logging.error(f"[ANSWER_AGGREGATOR] Error: {e}")

    return False
