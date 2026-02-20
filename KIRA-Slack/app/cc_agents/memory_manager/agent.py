"""
메모리 관리 에이전트 (Memory Manager Agent)

이 모듈은 memories 폴더를 관리하고, 정보를 체계적으로 저장하며,
index.md 파일을 자동으로 업데이트합니다.
"""

import logging
import os

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from app.config.settings import get_settings


def create_system_prompt(state_prompt: str, memories_path: str) -> str:
    """Memory manager를 위한 system prompt 생성

    Args:
        state_prompt: create_state_prompt()로 생성된 현재 상태 프롬프트
        memories_path: memories 폴더 절대 경로

    Returns:
        str: 메모리 관리를 위한 system prompt
    """
    settings = get_settings()
    bot_role = settings.BOT_ROLE or ""

    # 직군/역할 섹션 (설정된 경우에만)
    role_section = ""
    if bot_role:
        role_section = f"""

## 회사에서의 역할
<bot_role>
{bot_role}
이 역할과 관련된 정보를 우선적으로 저장하세요.
</bot_role>"""

    system_prompt = f"""당신은 Slack에서 상주하는 가상 직원 에이전트를 위해 기억을 관리하는 메모리 에이전트입니다.

{state_prompt}

# 기본 지침
가상 직원 에이전트의 다음 답변에 참고할 정보를 {memories_path}에 저장합니다.
{role_section}

## 워크플로우
<workflow>
1. 반드시 `slack-memory-store` skill을 사용하여 메모리를 관리합니다.
2. 전달받은 정보를 분석하고, 적절한 메타데이터를 추출합니다.
3. add_memory.py 스크립트를 사용하여 자동 분류 및 저장합니다.
4. 주기적으로 update_index.py를 실행하여 인덱스를 갱신합니다.
</workflow>

## 핵심 행동 원칙
<important_actions>
- 소속 팀 동료와 관련된 사항은 반드시 저장합니다.
- 채널 정보, 유저 정보, 한글 이름을 메타데이터에 포함합니다.
- 프로젝트는 프로젝트 명으로 저장하세요.
- tags를 적극 활용하세요.
- 중복 내용은 저장하지 마세요.
</important_actions>

## 가드레일 정책
<guardrails>
- {memories_path} 외부 접근 금지
- 스케줄링 요청은 저장 제외
- 가상 직원 정체성 정보는 저장 제외
</guardrails>"""

    return system_prompt


async def call_memory_manager(
    query: str,
) -> str:
    """
    메모리 관리 에이전트를 실행합니다.

    Args:
        query: 메모리 저장 요청 쿼리

    Returns:
        str: 에이전트 실행 결과
    """
    settings = get_settings()
    base_dir = settings.FILESYSTEM_BASE_DIR or os.getcwd()
    memories_path = os.path.join(base_dir, "memories")

    # memories 폴더가 없으면 생성
    os.makedirs(memories_path, exist_ok=True)

    # state_prompt 생성
    from app.cc_agents.state_prompt import create_state_prompt
    state_prompt = create_state_prompt()

    system_prompt = create_system_prompt(state_prompt, memories_path)

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=settings.MODEL_FOR_MODERATE,
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
        cwd=os.getcwd(),
        max_buffer_size=10 * 1024 * 1024
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(query)

            result_message = ""
            async for message in client.receive_response():

                # from devtools import pprint
                # pprint(message)

                if isinstance(message, ResultMessage):
                    result_message = message.result
                    logging.info(f"[MEMORY_MANAGER] Result: {result_message[:100]}...")
                    break

            return result_message if result_message else "메모리 작업을 완료할 수 없었습니다."

    except Exception as e:
        logging.error(f"[MEMORY_MANAGER] Error: {e}")
        return f"메모리 작업 중 오류가 발생했습니다: {str(e)}"
