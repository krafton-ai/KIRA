"""
Proactive Confirm Agent

사용자 응답이 pending confirm에 대한 답변인지 확인하는 에이전트
"""

import logging
import os
from typing import Tuple, Optional, Dict, Any

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from app.cc_utils.confirm_db import (
    get_channel_pending_confirms,
    update_confirm_response,
)
from app.config.settings import get_settings


def create_system_prompt() -> str:
    """Proactive confirm을 위한 system prompt 생성

    Returns:
        str: Proactive confirm을 위한 system prompt
    """
    system_prompt = """당신은 사용자의 응답이 확인 요청에 대한 승인인지 판단하는 에이전트입니다.

## 핵심 행동 원칙
<important_actions>
1. 원래 사용자 요청, 봇의 확인 메시지, 현재 사용자 응답을 모두 고려합니다.

2. 승인으로 간주되는 응답:
   - "예", "네", "응", "ㅇㅇ", "ㅇ", "yes", "ok", "okay"
   - "부탁해", "도와줘", "그래", "좋아", "ㄱㄱ"
   - "해줘", "하자", "가능해", "가능"

3. 거부로 간주되는 응답:
   - "아니", "아니요", "노", "no", "nope", "ㄴㄴ", "ㄴ"
   - "괜찮아", "됐어", "필요없어", "안돼"
   - 확인 메시지와 무관한 새로운 질문/대화

4. 애매한 경우는 거부로 처리합니다.
</important_actions>

## 출력 형식
<output_format>
승인: "true" 출력
거부: "false" 출력
</output_format>"""

    return system_prompt


async def call_proactive_confirm(
    user_text: str,
    channel_id: str,
    user_id: str,
    thread_ts: str = None
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Proactive confirm 에이전트를 실행합니다.

    Args:
        user_text: 사용자 메시지
        channel_id: 채널 ID
        user_id: 사용자 ID
        thread_ts: 스레드 타임스탬프 (스레드 격리용)

    Returns:
        Tuple[bool, Optional[Dict]]: (승인 여부, original_message)
        - (True, original_message): 승인됨, original_message 처리 필요
        - (False, None): 거부되거나 pending confirm 없음
    """
    settings = get_settings()

    # 1. pending confirm 조회 (thread_ts로 격리)
    pending_confirms = get_channel_pending_confirms(channel_id, user_id, thread_ts)

    if not pending_confirms:
        logging.info(f"[PROACTIVE_CONFIRM] No pending confirms for user {user_id} in channel {channel_id}")
        return False, None

    # 가장 최근 confirm 사용
    confirm = pending_confirms[0]
    confirm_id = confirm["confirm_id"]

    logging.info(f"[PROACTIVE_CONFIRM] Found pending confirm: {confirm_id}, message: '{confirm['confirm_message']}'")

    # 2. 사용자 응답이 승인인지 거부인지 판단
    system_prompt = create_system_prompt()

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

    try:
        async with ClaudeSDKClient(options=options) as client:
            # DB에서 원래 사용자 요청 텍스트 추출
            original_user_text = confirm["original_request_text"]

            query = f"""다음 정보를 확인하세요:

**원래 사용자 요청:** {original_user_text}
**봇의 확인 메시지:** {confirm['confirm_message']}
**현재 사용자 응답:** {user_text}

사용자 응답이 승인인지 거부인지 판단하세요.

승인이면 "true"를 반환하세요.
거부이면 "false"를 반환하세요.
"""

            await client.query(query)

            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    result_text = message.result.strip().lower()
                    logging.info(f"[PROACTIVE_CONFIRM] Response: {result_text}")

                    approved = "true" in result_text

                    if approved:
                        # 승인: DB 업데이트 + original_message 복원
                        update_confirm_response(
                            confirm_id=confirm_id,
                            user_id=user_id,
                            approved=True,
                            response=user_text
                        )

                        # DB에서 복원한 original_message (현재 컨텍스트는 cc_slack_handlers에서 처리)
                        reconstructed_message = {
                            "user_text": confirm["original_request_text"],
                            "user_id": confirm["user_id"],
                            "user_name": confirm["user_name"],
                            "channel_id": confirm["channel_id"]
                            # message_ts, thread_ts는 cc_slack_handlers에서 현재 컨텍스트로 설정됨
                        }

                        logging.info(f"[PROACTIVE_CONFIRM] Approved! Returning reconstructed original_message")
                        return True, reconstructed_message
                    else:
                        # 거부: DB 업데이트하여 rejected 상태로 변경
                        update_confirm_response(
                            confirm_id=confirm_id,
                            user_id=user_id,
                            approved=False,
                            response=user_text
                        )
                        logging.info(f"[PROACTIVE_CONFIRM] Rejected, marked as rejected in DB")
                        return False, None

    except Exception as e:
        logging.error(f"[PROACTIVE_CONFIRM] Error: {e}")

    return False, None
