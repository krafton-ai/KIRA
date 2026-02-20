"""
Confluence 페이지 요약 에이전트 (Confluence Summarizer)

여러 Confluence 페이지 업데이트를 분석하여 중요한 정보만 추출하고 요약합니다.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)


async def save_to_memory(content: str) -> None:
    """
    Confluence 페이지 업데이트 내용을 메모리 큐에 추가합니다.

    Args:
        content: 저장할 내용 (중요한 페이지 업데이트 요약)
    """
    try:
        from app.queueing_extended import enqueue_memory_job

        memory_query = f"""다음은 최근 Confluence 페이지 업데이트 내용입니다. 참고할 만한 정보가 있다면 저장하세요.

{content}

`slack-memory-store` skill을 사용해서 이 정보를 적절한 카테고리에 분류하고 저장하세요.
소속 팀 동료와 관련된 사항은 반드시 저장합니다.
"""

        # 메모리 큐에 작업 추가 (순차 처리됨)
        await enqueue_memory_job({
            "memory_query": memory_query
        })
        logging.info(f"[CONFLUENCE_SUMMARIZER] Memory job enqueued")
    except Exception as e:
        logging.error(f"[CONFLUENCE_SUMMARIZER] Memory enqueue failed: {e}")


def create_system_prompt(state_prompt: str, bot_name: str, bot_role: str = "") -> str:
    """Confluence summarizer를 위한 system prompt 생성

    Args:
        state_prompt: create_state_prompt()로 생성된 현재 상태 프롬프트
        bot_name: 봇 이름
        bot_role: 봇의 회사에서의 역할

    Returns:
        str: 에이전트의 행동 원칙과 도구 사용 원칙을 포함한 system prompt
    """
    # 직군/역할 섹션 (설정된 경우에만)
    role_section = ""
    if bot_role:
        role_section = f"""

## 회사에서의 역할
<bot_role>
{bot_role}
이 역할과 관련된 정보를 우선적으로 저장하세요.
</bot_role>"""

    system_prompt = f"""당신은 Slack으로 커뮤니케이션 하는 가상 상주 직원 {bot_name}님 입니다.

# 기본 지침
Confluence 페이지 업데이트를 분석하고 중요한 정보만 추출하는 에이전트입니다.
여러 Confluence 페이지 업데이트를 받아서 **업무상 중요한 내용만** 필터링하고 정리합니다.
후임 에이전트가 다음 대화에서 참고할 수 있도록 중요한 페이지 업데이트만 정리하여 전달하는 것이 핵심입니다.
{role_section}

{state_prompt}

## 워크플로우
<workflow>
1. 전달받은 Confluence 페이지 업데이트 배치를 분석합니다.
2. 필요시 Rovo MCP 도구로 페이지 본문 전체를 조회합니다.
3. 각 페이지의 중요도를 판단 기준에 따라 평가합니다.
4. 중요한 페이지 업데이트만 선별하여 정리합니다.
</workflow>

## 도구 사용 원칙
<how_to_use_tool>
1. 먼저 `confluence-deep-reader` skill을 사용하고 워크플로우에 따라 Rovo MCP 도구를 사용하세요.
2. 제목과 수정 정보만으로 중요도를 판단하기 어려운 경우, 반드시 페이지 본문을 조회하여 정확하게 평가하세요.
3. 페이지 ID를 사용하여 도구 호출 시 정확한 ID를 전달하세요.
4. 페이지 본문 조회는 중요도 판단이 명확하지 않은 경우에만 사용하여 효율성을 높이세요.
5. 파일을 만들어야 할 경우 반드시 `FILESYSTEM_BASE_DIR/checkers/tmp/` 디렉토리에 임시로 생성하고, 작업 완료 후 삭제하세요.
</how_to_use_tool>

## 핵심 행동 원칙
<important_actions>
**중요한 페이지 업데이트 판단 기준:**
- 소속 팀 동료 관련 사항
- 프로젝트 계획, 일정, 마일스톤 변경
- 기술 문서, API 명세, 아키텍처 변경
- 회의록, 의사결정 기록
- 정책, 가이드라인, 프로세스 변경
- 팀 공지사항, 중요 이슈 트래킹
</important_actions>

## 출력 형식
<output_format>
중요한 페이지 업데이트가 있는 경우:
- 업데이트 내용을 상세하게 정리하여 카테고리별로 구분하여 정리합니다.
- 각 페이지의 제목, URL, 수정자, 수정 시간, 핵심 변경 내용을 포함합니다.

중요한 페이지 업데이트가 없는 경우:
- "중요한 페이지 업데이트가 없습니다."만 출력합니다.
</output_format>

## 가드레일 정책
<guardrails>
**필터링 제외 항목:**
- 개인 메모, 임시 작업 페이지는 중요하지 않습니다.
- 사소한 오타 수정, 포맷 변경은 저장하지 마세요.
- 테스트 페이지는 제외하세요.
- 중복/반복되는 내용은 제외하세요.

**파일 시스템 접근 제한:**
- FILESYSTEM_BASE_DIR 외부의 파일이나 디렉토리에 절대 접근하지 마세요
- 시스템 파일, 홈 디렉토리, 설정 파일 등을 읽거나 수정하는 것은 엄격히 금지됩니다
- 파일 작업은 반드시 FILESYSTEM_BASE_DIR 내부로 제한됩니다
</guardrails>"""

    return system_prompt


async def call_confluence_summarizer(
    pages: List[Dict[str, Any]]
) -> Optional[str]:
    """
    Confluence 페이지 배치를 분석하여 중요한 내용만 요약합니다.

    Args:
        pages: 페이지 리스트 (id, title, version, spaceId 포함)

    Returns:
        Optional[str]: 메모리 저장용 쿼리 (중요한 내용이 없으면 None)
    """
    if not pages:
        return None

    # settings와 bot_name 먼저 가져오기
    from app.cc_agents.state_prompt import create_state_prompt
    from app.config.settings import get_settings

    settings = get_settings()
    bot_name = settings.BOT_NAME or "봇"
    bot_role = settings.BOT_ROLE or ""

    # state_prompt 생성 (slack_data, message_data 없이)
    state_prompt = create_state_prompt()

    system_prompt = create_system_prompt(state_prompt, bot_name, bot_role)

    # 페이지 리스트를 텍스트로 변환
    pages_text = ""
    for idx, page in enumerate(pages, 1):
        page_id = page.get("id", "")
        title = page.get("title", "")
        version = page.get("version", {})
        modified_date = version.get("createdAt", "")
        modified_by_id = version.get("authorId", "Unknown")
        modified_by_email = version.get("authorEmail", "")
        space_id = page.get("spaceId", "")
        page_url = f"{settings.ATLASSIAN_CONFLUENCE_SITE_URL}/wiki/spaces/{space_id}/pages/{page_id}"

        # 수정자 표시 (이메일 우선, 없으면 ID)
        modified_by = modified_by_email if modified_by_email else modified_by_id

        pages_text += f"""
페이지 {idx}:
페이지 ID: {page_id}
제목: {title}
URL: {page_url}
수정자: {modified_by}
수정 시간: {modified_date}

---
"""

    user_query = f"""다음 {len(pages)}개의 Confluence 페이지 업데이트를 분석하세요:

{pages_text}

반드시 소속 팀 동료와 관련된 사항은 누락하지마세요."""

    # Atlassian MCP 서버 설정 (remote)
    mcp_servers = {
        "atlassian": {
            "command": "npx",
            "args": ["mcp-cache", "npx", "-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
        }
    }

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
            "Write",
            "Edit",
            "NotebookEdit",
        ],
        setting_sources=['project'],
        cwd=os.getcwd(),
        mcp_servers=mcp_servers,
    )

    session_id = None
    result_message = ""

    # Context overflow 시 /compact 후 재시도 (같은 client 유지, 최대 2회)
    max_retries = 2

    async with ClaudeSDKClient(options=options) as client:
        for attempt in range(max_retries + 1):
            try:
                # 첫 시도는 새 세션, 재시도는 compact된 세션 이어서
                if session_id:
                    await client.query(user_query, session_id)
                else:
                    await client.query(user_query)

                async for message in client.receive_response():
                    if hasattr(message, 'subtype') and message.subtype == 'init':
                        session_id = message.data.get('session_id')
                        logging.info(f"[CONFLUENCE_SUMMARIZER] Session ID: {session_id}")

                    if isinstance(message, ResultMessage):
                        if "API Error" in message.result and "413" in message.result:
                            raise Exception(f"Context overflow in ResultMessage: {message.result}")

                        result_message = message.result.strip()
                        logging.info(f"[CONFLUENCE_SUMMARIZER] Result: {result_message[:100]}...")
                        break

                # 성공하면 루프 종료
                break

            except Exception as e:
                error_str = str(e)
                error_msg = error_str.lower()

                is_context_error = any([
                    "prompt is too long" in error_msg,
                    "context overflow" in error_msg,
                    "413" in error_msg,
                ])

                if is_context_error and attempt < max_retries:
                    logging.warning(f"[CONFLUENCE_SUMMARIZER] Context overflow detected (attempt {attempt + 1}/{max_retries}), executing /compact...")

                    # 같은 client로 /compact 실행 (session_id 전달)
                    await client.query("/compact", session_id)
                    async for msg in client.receive_response():
                        if isinstance(msg, ResultMessage):
                            logging.info(f"[CONFLUENCE_SUMMARIZER] /compact executed successfully")
                            break

                    # 같은 client, 원래 query로 재시도
                    continue
                else:
                    # 재시도 횟수 초과 또는 다른 에러
                    logging.error(f"[CONFLUENCE_SUMMARIZER] Error occurred: {e}")
                    return None

    # while 루프 정상 종료 후 결과 반환
    if result_message == "중요한 페이지 업데이트가 없습니다." or not result_message:
        logging.info("[CONFLUENCE_SUMMARIZER] No important pages found")
        return None

    return result_message
