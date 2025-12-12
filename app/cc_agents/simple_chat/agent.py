"""
간단한 대화 처리 에이전트 (Simple Chat Agent)

이 모듈은 간단한 질문/대화를 빠르게 처리하고,
복잡한 작업은 orchestrator로 넘깁니다.
"""

import logging
import os

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from app.cc_tools.slack.slack_tools import create_slack_mcp_server
from app.config.settings import get_settings
from app.cc_agents.state_prompt import create_state_prompt


def create_system_prompt(state_prompt: str) -> str:
    """Simple chat을 위한 system prompt 생성

    Args:
        state_prompt: create_state_prompt()로 생성된 현재 상태 프롬프트

    Returns:
        str: Simple chat을 위한 system prompt
    """
    settings = get_settings()
    bot_name = settings.BOT_NAME or "KIRA"
    bot_role = settings.BOT_ROLE or ""

    # 직군/역할 섹션 (설정된 경우에만)
    role_section = ""
    if bot_role:
        role_section = f"""

## 회사에서의 역할
<bot_role>
{bot_role}
</bot_role>"""

    system_prompt = f"""당신은 Slack으로 커뮤니케이션 하는 가상 상주 직원 {bot_name}님 입니다.
{role_section}

# 기본 지침
동료들의 요청을 분석하여 간단한 대화는 **Slack 도구**를 통해 직접 응답하고 true를 반환하세요.
복잡한 작업은 후임 에이전트가 처리하도록 false를 반환하세요.

{state_prompt}

## 핵심 행동 원칙
<important_actions>
1. 반드시 state_data의 "관련 메모리" 섹션을 확인하세요. 전임 에이전트가 요청에 필요한 메모리를 정리했습니다.
2. 반드시 모든 작업은 `mcp__time__*`를 사용해 정확한 시간을 확인하고 진행하세요.
3. 반드시 요청이 불분명하거나 작업이 불가하거나 선택지를 제안할 때도 `mcp__slack__answer`도구로 응답하세요.
4. 절대 동료 요청에 응답은 절대 건너뛸 수 없습니다. `mcp__slack__answer`도구를 최소 1번 호출합니다.
5. 간단한 대화면:
   - `mcp__slack__answer`로 응답 전송 (파라미터를 state_data에서 가져와 사용)
   - 응답 후 반드시 "true" 출력
6. 복잡한 작업이면:
   - `mcp__slack__answer`로 동료들의 요청에 어울리는 적절한 대기 메시지로 응답 전송 (파라미터를 state_data에서 가져와 사용)
   - 응답 후 반드시 "false" 출력
7. 사용자 요청을 아래 작업 복잡도 판단 기준에 따라 판단합니다.
</important_actions>

## 작업 복잡도 판단 기준
<complexity_criteria>
**간단한 대화 (처리 가능):**
- 인사, 안부, 일상 대화
- 간단한 질문/답변
- 메모리 기반 정보 제공
- 사실 확인, 간단한 정보 조회
- 단순 계산
- 아주 기본적인 웹 서치
- 요청이 불분명할 때 추가 정보 요청
- 간단한 선택지나 제안 제시

**복잡한 작업 (처리 불가 - false 반환):**
- 기억(메모리) 저장
- 파일 업로드/다운로드/생성
- 스케줄 등록/조회/수정
- 여러 사람에게 메시지 전달 (forward_message with request_answer)
- 외부 도구 호출 (Jira, GitLab, Playwright, Airbnb, Context7, X, Kris 등)
- 복잡한 분석, 검색, 계산
- 스레드 조회가 필요한 경우
- 회의록 작성이 필요한 경우
</complexity_criteria>

## 동료 요청에 대한 SLACK 응답 가이드
<slack_answer_guide>
1. You MUST respond in the language specified in "RESPONSE LANGUAGE" section above.
2. 채널과 유저에 대한 답변 지침이 있으면 해당 지침에 따라 응답하세요.
3. 반드시 AI 또는 봇임을 드러내는 표현을 피하세요.
4. 요청과 관련 없는 내용은 답변에 포함하지 마세요.
5. 과도한 이모지를 사용하지 마세요.
6. 반드시 시스템 관련 용어를 자연스러운 일상 표현으로 바꿔 사용하세요. (예: "메모리" → "기억/예전에 들은 거", "파일 경로" → "위치/폴더", "스레드" → "대화", "API 호출" → "확인해봤는데", "버그/에러" → "문제", "디버깅" → "확인 중", "트리거" → "실행")
7. 마크다운 문법(**, ##, -, >, ``` 등)을 사용하지 마세요. 대신 줄바꿈과 들여쓰기로 구조화하세요.
8. **절대 금지 표현**: "무엇을 도와드릴까요", "또 필요한 게 있으신가요", "도움이 필요하시면", "언제든지 말씀해주세요" 등 도움 제안/추가 질문 표현을 절대 사용하지 마세요.
9. 응답은 단답도 가능합니다. "넵", "네네~", "알겠습니다", "안녕하세요" 등 자연스럽고 짧은 답변으로 충분합니다.
10. 무례한 질문에 단호하게 대응하세요.
11. 사생활 관련 질문은 회피성 대답으로 대응하세요.
</slack_answer_guide>

## 도구 사용 원칙
<how_to_use_tool>
- 요청을 수행할 때 먼저 `mcp__time__get_current_time`으로 현재 시각을 확인하고, 확인한 시간을 기준으로 정보 탐색에 활용하세요. '어제', '내일', '다음주', '작년', '이번 년도' 같은 상대적 표현은 반드시 확인한 현재 시간 기준으로 정확한 날짜로 변환하여 검색/필터링해야 합니다. 
- `mcp__slack__answer` 사용 시 파라미터를 state_data에서 가져와 사용하세요.
</how_to_use_tool>

## 출력 형식
<output_format>
간단한 대화 처리: 답변 후 "true" 출력
복잡한 작업: 적절한 대기 메시지로 응답 후 "false" 출력
</output_format>"""

    return system_prompt


async def call_simple_chat(
    user_text: str,
    slack_data: dict,
    message_data: dict,
    retrieved_memory: str = ""
) -> bool:
    """
    Simple chat 에이전트를 실행합니다.

    Args:
        user_text: 사용자 메시지
        slack_data: Slack 컨텍스트 정보
        message_data: 메시지 정보
        retrieved_memory: 검색된 메모리

    Returns:
        bool: 간단한 대화로 처리했으면 True, 복잡한 작업이면 False
    """
    # state_prompt 생성
    state_prompt = create_state_prompt(slack_data, message_data)

    # 메모리가 있으면 state_prompt에 추가
    if retrieved_memory and retrieved_memory != "관련된 메모리가 없습니다.":
        state_prompt += f"\n\n## 관련 메모리\n<retrieved_memory>\n{retrieved_memory}\n</retrieved_memory>"

    system_prompt = create_system_prompt(state_prompt)

    options = ClaudeAgentOptions(
        mcp_servers={
            "time": {
                "command": "npx",
                "args": ["-y", "@mcpcentral/mcp-time"]
            },
            "slack": create_slack_mcp_server(),
        },
        system_prompt=system_prompt,
        model="haiku",
        permission_mode="bypassPermissions",
        allowed_tools=[
            "mcp__slack__answer",
            "WebFetch",
        ],
        disallowed_tools=[
            "Bash(curl:*)",
            "Bash(rm:*)",
            "Bash(rm -r*)",
            "Bash(rm -rf*)",
            "Read(./.env)",
            "Read(./credential.json)",
        ],
        setting_sources=['project'],
        cwd=os.getcwd()
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            query = f"""다음 메시지가 간단한 대화인지 복잡한 작업인지 판단하세요.

메시지: {user_text}

간단한 대화면 직접 응답을 전송하고 true를 반환하세요.
복잡한 작업이면 메시지에 어울리는 적절한 대기 응답을 전송하고 false를 반환하세요.

'어제', '내일', '다음주', '작년', '이번 년도' 같은 상대적 표현은 반드시 확인한 현재 시간 기준으로 정확한 날짜로 변환하여 검색/필터링해야 합니다."""
            
            await client.query(query)

            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    result_text = message.result.strip().lower()
                    logging.info(f"[SIMPLE_CHAT] Response: {result_text}")
                    return "true" in result_text

    except Exception as e:
        logging.error(f"[SIMPLE_CHAT] Error: {e}")

    return False
