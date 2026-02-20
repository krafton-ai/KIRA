"""
Jira 티켓 추출 에이전트 (Jira Task Extractor)

할당된 Jira 티켓을 분석하여 중요한 티켓을 추출하고 DB에 저장합니다.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from app.cc_agents.memory_retriever.agent import call_memory_retriever
from app.cc_tools.jira_tasks import create_jira_tasks_mcp_server
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)


def create_system_prompt(state_prompt: str, bot_name: str) -> str:
    """Jira task extractor를 위한 system prompt 생성

    Args:
        state_prompt: create_state_prompt()로 생성된 현재 상태 프롬프트
        bot_name: 봇 이름

    Returns:
        str: 에이전트의 행동 원칙과 도구 사용 원칙을 포함한 system prompt
    """
    system_prompt = f"""당신은 Slack으로 커뮤니케이션 하는 가상 상주 직원 {bot_name}님 입니다.

# 기본 지침
전달받은 Jira 티켓들을 분석하여 **당신이 해야 할 작업**을 추출하고 DB에 저장하세요.

{state_prompt}

## 핵심 행동 원칙
<important_actions>
1. 전달받은 Jira 티켓들을 분석하여 당신이 해야 할 작업을 추출합니다.
2. 필요시 Rovo MCP 도구로 티켓 상세 정보를 조회합니다.
3. 해야 할 작업이 있으면 `mcp__jira_tasks__add_jira_task`로 DB에 저장합니다.
4. 처리 결과를 요약하여 출력합니다.
</important_actions>

## 도구 사용 원칙
<how_to_use_tool>
1. 티켓 정보만으로 해야 할 작업을 파악하기 어려우면 Rovo MCP 도구로 상세 정보를 조회해야 합니다.
2. 티켓 보고자(reporter)의 user_id, user_name, channel_id는 retrieved_memory에서 찾아야 합니다.
   - 티켓에 reporter 이메일이 있으니, 그 이메일로 메모리를 검색하세요.
3. `mcp__jira_tasks__add_jira_task`의 `text` 파라미터는 다음 형식을 따라야 합니다:
   "{bot_name}님, [티켓키] 티켓을 통해 [작업명] 작업이 할당되었습니다. 작업을 수행하시고 [티켓키] 티켓을 Done 처리해주세요."
   예: "{bot_name}님, PROJ-123 티켓을 통해 코드 리뷰 작업이 할당되었습니다. 작업을 수행하시고 PROJ-123 티켓을 Done 처리해주세요."
4. 반드시 1개의 티켓에 여러 작업이 있으면 각각 **별도로** 저장해야 합니다.
5. user_id, user_name, channel_id를 모두 찾지 못하면 해당 작업은 저장하지 않습니다.
6. 모든 할당된 티켓은 당신이 처리해야 하는 것이므로, 각 티켓에서 해야 할 작업을 추출하세요.
7. 파일을 만들어야 할 경우 반드시 `FILESYSTEM_BASE_DIR/checkers/tmp/` 디렉토리에 임시로 생성하고, 작업 완료 후 삭제하세요.
</how_to_use_tool>

## 가드레일 정책
<guardrails>
**파일 시스템 접근 제한:**
- FILESYSTEM_BASE_DIR 외부의 파일이나 디렉토리에 절대 접근하지 마세요
- 시스템 파일, 홈 디렉토리, 설정 파일 등을 읽거나 수정하는 것은 엄격히 금지됩니다
- 파일 작업은 반드시 FILESYSTEM_BASE_DIR 내부로 제한됩니다
</guardrails>"""

    return system_prompt


async def call_jira_task_extractor(issues: List[Dict[str, Any]]) -> Optional[str]:
    """
    Jira 티켓 배치를 분석하여 해야 할 작업을 추출하고 DB에 저장합니다.

    Args:
        issues: 이슈 리스트 (key, fields 포함)

    Returns:
        Optional[str]: 처리 결과 요약 (할 일이 없으면 None)
    """
    if not issues:
        return None

    # settings와 bot_name 먼저 가져오기
    from app.cc_agents.state_prompt import create_state_prompt
    from app.config.settings import get_settings

    settings = get_settings()
    bot_name = settings.BOT_NAME or "봇"

    # 이슈 리스트를 텍스트로 변환
    issues_text = ""
    for idx, issue in enumerate(issues, 1):
        issue_key = issue.get("key", "")
        fields = issue.get("fields", {})

        summary = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "Unknown")
        priority = fields.get("priority", {}).get("name", "Medium")
        issue_type = fields.get("issuetype", {}).get("name", "Task")
        updated = fields.get("updated", "")
        created = fields.get("created", "")

        # 이슈 URL 생성
        issue_url = f"{settings.ATLASSIAN_JIRA_SITE_URL}/browse/{issue_key}"

        # Description 간략히 포함
        description = fields.get("description", "")
        description_preview = (
            description[:200] + "..."
            if description and len(description) > 200
            else description
        )

        # 담당자 정보
        assignee = fields.get("assignee", {})
        assignee_name = assignee.get("displayName", "없음") if assignee else "없음"
        assignee_email = assignee.get("emailAddress", "") if assignee else ""

        # 보고자 정보
        reporter = fields.get("reporter", {})
        reporter_name = reporter.get("displayName", "없음") if reporter else "없음"
        reporter_email = reporter.get("emailAddress", "") if reporter else ""

        issues_text += f"""
티켓 {idx}:
이슈 키: {issue_key}
제목: {summary}
URL: {issue_url}
상태: {status}
우선순위: {priority}
유형: {issue_type}
담당자(assignee): {assignee_name} <{assignee_email}>
보고자(reporter): {reporter_name} <{reporter_email}>
생성 시간: {created}
업데이트 시간: {updated}
설명 미리보기: {description_preview}

---
"""

    jira_task_memory_query = f"""다음 {len(issues)}개의 Jira 티켓과 관련된 모든 사람의 정보를 찾아 메모리를 취합해 알려주세요.
반드시 해당 채널과 요청 유저에 대한 **지침**과 정보(channel_id, user_id, user_name)를 포함하세요.

{issues_text}"""

    # 1. 메모리 검색 (jira task extractor 용)
    retrieved_memory = await call_memory_retriever(jira_task_memory_query)
    logging.info(
        f"[JIRA_TASK_EXTRACTOR] Memory retrieved: {retrieved_memory[:100] if retrieved_memory else 'None'}..."
    )

    state_prompt = create_state_prompt()

    # 메모리 추가
    state_prompt += f"\n\n## 관련 메모리\n<retrieved_memory>\n{retrieved_memory}\n</retrieved_memory>"

    system_prompt = create_system_prompt(state_prompt, bot_name)

    # 2. jira task extractor 호출
    query = f"""다음 {len(issues)}개의 Jira 티켓에서 당신이 해야 할 작업을 추출하여 DB에 저장하세요.

{issues_text}

각 티켓을 분석하여 구체적으로 해야 할 작업(코드 리뷰, 테스트 작성, 배포 등)을 추출하세요."""

    # Atlassian MCP 서버 설정 (remote)
    mcp_servers = {
        "atlassian": {
            "command": "npx",
            "args": ["mcp-cache", "npx", "-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"],
        },
        "jira_tasks": create_jira_tasks_mcp_server(),
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
        setting_sources=["project"],
        cwd=os.getcwd(),
        mcp_servers=mcp_servers,
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(query)

            result_message = ""
            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    result_message = message.result.strip()
                    logging.info(
                        f"[JIRA_TASK_EXTRACTOR] Result: {result_message[:100]}..."
                    )
                    break

            # Return None if no tasks
            if not result_message or (
                "no task" in result_message.lower() and "found" in result_message.lower()
            ):
                logging.info("[JIRA_TASK_EXTRACTOR] No tasks extracted")
                return None

            return result_message

    except Exception as e:
        logging.error(f"[JIRA_TASK_EXTRACTOR] Error: {e}")
        return None
