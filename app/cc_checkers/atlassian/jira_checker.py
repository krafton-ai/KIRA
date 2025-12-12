"""
Jira Checker using Rovo MCP
Rovo MCP를 통해 Jira 이슈를 모니터링하고 데이터 수집
"""

import asyncio
import logging
import os
from pprint import pprint
from typing import List, Dict, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def fetch_assigned_issues() -> List[Dict[str, Any]]:
    """
    Rovo MCP를 사용하여 자기에게 할당된 Jira 티켓 조회

    Returns:
        할당된 이슈 리스트
    """
    if not settings.ATLASSIAN_ENABLED:
        logger.error("[JIRA_CHECKER] Atlassian MCP is not enabled")
        return []

    prompt = """Jira 데이터 수집 에이전트입니다.

**작업 지시:**
1. `mcp__atlassian__*` 도구로 나에게 할당된 Jira 티켓 조회
2. 완료되지 않은 (Done이 아닌) 이슈만
3. 최대 10개

**출력 형식:**
JSON 배열로만 응답 (설명 없이):
```json
[
  {
    "key": "PROJ-123",
    "fields": {
      "summary": "...",
      "status": {"name": "..."},
      "priority": {"name": "..."},
      "assignee": {"displayName": "...", "emailAddress": "..."},
      "reporter": {"displayName": "...", "emailAddress": "..."},
      "created": "...",
      "updated": "...",
      "description": "...",
      "issuetype": {"name": "..."},
      "project": {"key": "...", "name": "..."}
    }
  }
]
```

**주의:** 이슈 없으면 빈 배열 [] 반환"""

    # Atlassian MCP 서버 설정 (remote)
    mcp_servers = {
        "atlassian": {
            "command": "npx",
            "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
        }
    }

    options = ClaudeAgentOptions(
        system_prompt=prompt,
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
        mcp_servers=mcp_servers,
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query("mcp__atlassian 도구를 사용해서 할당된 Jira 티켓을 조회하고 JSON으로 반환해주세요.")

            result_message = ""
            async for message in client.receive_response():
                pprint(message)
                if isinstance(message, ResultMessage):
                    result_message = message.result.strip()
                    logger.info(f"[JIRA_CHECKER] MCP result received: {len(result_message)} chars")
                    break

            if not result_message:
                logger.info("[JIRA_CHECKER] No result from MCP")
                return []

            # JSON 파싱
            import json

            # ```json ``` 블록 제거
            if "```json" in result_message:
                result_message = result_message.split("```json")[1].split("```")[0].strip()
            elif "```" in result_message:
                result_message = result_message.split("```")[1].split("```")[0].strip()

            issues = json.loads(result_message)

            if not isinstance(issues, list):
                logger.error(f"[JIRA_CHECKER] Invalid response format: expected list, got {type(issues)}")
                return []

            logger.info(f"[JIRA_CHECKER] Fetched {len(issues)} assigned issues")
            if len(issues) == 0:
                logger.info(f"[JIRA_CHECKER] Raw response (empty): {result_message[:500]}")
            return issues

    except json.JSONDecodeError as e:
        logger.error(f"[JIRA_CHECKER] JSON parsing error: {e}")
        logger.error(f"[JIRA_CHECKER] Raw result: {result_message[:1000]}")
        return []
    except Exception as e:
        logger.error(f"[JIRA_CHECKER] Error fetching issues: {e}", exc_info=True)
        return []


async def process_issues_batch(issues: List[Dict[str, Any]]):
    """
    여러 이슈를 배치로 처리 (백그라운드)

    Args:
        issues: 이슈 리스트
    """
    logger.info(f"[JIRA_PROCESSOR] Processing {len(issues)} issues in background")

    for idx, issue in enumerate(issues, 1):
        issue_key = issue.get("key", "")
        fields = issue.get("fields", {})

        summary = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "")
        priority = fields.get("priority", {}).get("name", "")
        updated = fields.get("updated", "")

        # 이슈 URL 생성
        issue_url = f"{settings.ATLASSIAN_JIRA_SITE_URL}/browse/{issue_key}"

        logger.info(f"[JIRA_PROCESSOR] [{idx}/{len(issues)}] {issue_key}: {summary}")
        logger.info(
            f"[JIRA_PROCESSOR] [{idx}/{len(issues)}] Status: {status}, Priority: {priority}"
        )
        logger.info(f"[JIRA_PROCESSOR] [{idx}/{len(issues)}] URL: {issue_url}")
        logger.info(f"[JIRA_PROCESSOR] [{idx}/{len(issues)}] Updated: {updated}")

    # 1. DB에 이미 있는 티켓 제외
    from app.cc_checkers.atlassian.jira_agent import call_jira_task_extractor
    from app.cc_utils.jira_tasks_db import (
        get_pending_tasks,
        complete_task,
        get_existing_issue_keys,
    )
    from app.queueing_extended import enqueue_message

    existing_issue_keys = get_existing_issue_keys()
    new_issues = [
        issue for issue in issues if issue.get("key") not in existing_issue_keys
    ]

    if not new_issues:
        logger.info(
            f"[JIRA_PROCESSOR] All {len(issues)} issues already exist in DB, skipping agent call"
        )
    else:
        logger.info(
            f"[JIRA_PROCESSOR] Found {len(new_issues)} new issues out of {len(issues)} total"
        )

        # 2. 에이전트 호출하여 새로운 티켓에서 할 일 추출 및 DB에 저장
        result = await call_jira_task_extractor(new_issues)

        if result:
            logger.info(f"[JIRA_PROCESSOR] Jira task extraction result:")
            logger.info(f"[JIRA_PROCESSOR] {result}")
        else:
            logger.info(f"[JIRA_PROCESSOR] No tasks extracted from tickets")

    # 3. DB에서 pending tasks 조회 (항상 수행)
    pending_tasks = get_pending_tasks()

    if pending_tasks:
        logger.info(f"[JIRA_PROCESSOR] Found {len(pending_tasks)} pending tasks")

        # 4. Slack 큐에 메시지 enqueue
        for task in pending_tasks:
            task_id = task["id"]
            user_id = task.get("user")
            text = task.get("text")
            channel_id = task.get("channel")

            # user, text, channel이 모두 있는 경우에만 큐에 추가
            if user_id and text and channel_id:
                # Slack 큐에 추가 (웹 인터페이스와 동일한 패턴)
                await enqueue_message({
                    "text": text,
                    "channel": channel_id,
                    "ts": "",
                    "user": user_id,
                    "thread_ts": None,
                })
                logger.info(f"[JIRA_PROCESSOR] Enqueued task {task_id} to user {user_id}")

                # 5. Task를 완료 처리
                complete_task(task_id)
            else:
                logger.warning(
                    f"[JIRA_PROCESSOR] Task {task_id} missing user/text/channel, skipping"
                )

        logger.info(f"[JIRA_PROCESSOR] Processed {len(pending_tasks)} tasks")
    else:
        logger.info(f"[JIRA_PROCESSOR] No pending tasks to process")

    logger.info(f"[JIRA_PROCESSOR] Completed processing {len(issues)} issues")


async def check_jira_updates():
    """
    할당된 Jira 티켓 체크 및 배치 처리
    스케줄러에서 주기적으로 호출됨
    """
    if not settings.ATLASSIAN_ENABLED:
        logger.info("[JIRA_CHECKER] Atlassian MCP is not enabled")
        return

    if not settings.JIRA_CHECK_ENABLED:
        logger.info("[JIRA_CHECKER] Jira check is not enabled")
        return

    logger.info("[JIRA_CHECKER] Checking assigned Jira issues...")

    try:
        issues = await fetch_assigned_issues()

        if issues:
            logger.info(
                f"[JIRA_CHECKER] Found {len(issues)} assigned issues, starting background processing"
            )
            # 백그라운드 태스크로 처리
            asyncio.create_task(process_issues_batch(issues))
        else:
            logger.info("[JIRA_CHECKER] No assigned issues found")

    except Exception as e:
        logger.error(f"[JIRA_CHECKER] Error in check_jira_updates: {e}", exc_info=True)
