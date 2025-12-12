"""
메모리 검색 에이전트 (Memory Retriever Agent)

이 모듈은 사용자 쿼리와 관련된 메모리를 검색하고 취합하여 반환합니다.
"""

import logging
import os
from typing import Optional

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from app.config.settings import get_settings


def create_system_prompt(state_prompt: str, memories_path: str) -> str:
    """Memory retriever를 위한 system prompt 생성

    Args:
        state_prompt: create_state_prompt()로 생성된 현재 상태 프롬프트
        memories_path: memories 폴더 절대 경로

    Returns:
        str: 메모리 검색을 위한 system prompt
    """
    system_prompt = f"""당신은 Slack에서 상주하는 가상 직원 에이전트의 작업을 위해 메모리를 취합하는 에이전트입니다.

{state_prompt}

# 기본 지침
`slack-memory-retrieval` skill을 사용하여 답변에 필요한 컨텍스트를 조회합니다.

## 워크플로우
<workflow>
1. 대화 컨텍스트 분석 (채널, 유저, 키워드)
2. 항상 {memories_path}/index.md 먼저 읽기
3. 관련 메모리 파일 로드 (channels, users, projects 등)
4. 정보를 자연스럽게 종합하여 답변
</workflow>

## 메모리 탐색 전략
<retrieval_strategy>
- 채널 대화 → channels/ 먼저 확인
- DM 대화 → users/ 먼저 확인  
- 프로젝트 질문 → projects/ 확인
- 결정사항 질문 → decisions/ 확인
- related_to 메타데이터 따라가기
</retrieval_strategy>

## 가드레일 정책
<guidelines>
- 출처를 명시하지 말고 자연스럽게 통합
- 채널/유저 선호도 적용
- 필요한 것만 로드 (과도한 조회 금지)
- {memories_path} 외부 접근 금지
</guidelines>"""

    return system_prompt


async def call_memory_retriever(
    search_query: str,
    slack_data: Optional[dict] = None,
    message_data: Optional[dict] = None
) -> str:
    """
    메모리 검색 에이전트를 실행합니다.

    Args:
        search_query: 메모리 검색 쿼리
        slack_data: Slack 컨텍스트 정보 (선택)
        message_data: 메시지 정보 (선택)

    Returns:
        str: 취합된 메모리 내용
    """
    settings = get_settings()
    base_dir = settings.FILESYSTEM_BASE_DIR or os.getcwd()
    memories_path = os.path.join(base_dir, "memories")

    # memories 폴더가 없으면 빈 결과 반환
    if not os.path.exists(memories_path):
        logging.info(f"[MEMORY_RETRIEVER] No memories folder found")
        return "관련된 메모리가 없습니다."

    # state_prompt 생성
    from app.cc_agents.state_prompt import create_state_prompt
    state_prompt = create_state_prompt(slack_data, message_data)

    system_prompt = create_system_prompt(state_prompt, memories_path)

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
            "Write",
            "Edit",
            "NotebookEdit",
        ],
        setting_sources=['project'],
        cwd=os.getcwd(),
        max_buffer_size=10 * 1024 * 1024
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(search_query)

            result_message = ""
            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    result_message = message.result
                    logging.info(f"[MEMORY_RETRIEVER] Result: {result_message[:100]}...")
                    break

            return result_message if result_message else "관련된 메모리가 없습니다."

    except Exception as e:
        logging.error(f"[MEMORY_RETRIEVER] Error: {e}")
        return "관련된 메모리가 없습니다."
