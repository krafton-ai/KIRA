"""
Email Checker for Microsoft 365 (Lokka MCP)
Outlook 이메일을 주기적으로 체크하고 LLM으로 처리하는 모듈

체커 컨셉: 설정한 MCP의 확장으로 주기적 작업 처리
- Operator: Lokka MCP 사용 (사용자 요청 처리)
- Checker: Lokka MCP 사용 (백그라운드 주기 작업)
"""

import asyncio
import json
import logging
import os
from typing import List, Dict, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage

from app.config.settings import get_settings

settings = get_settings()


async def fetch_new_emails() -> List[Dict[str, Any]]:
    """
    Lokka MCP를 사용하여 최신 읽지 않은 이메일 조회

    Returns:
        최신 이메일 리스트 (최대 10개)
    """
    if not settings.MS365_ENABLED:
        logging.error("[EMAIL_CHECKER] MS365 MCP is not enabled")
        return []

    # MCP 서버 설정 (Lokka - cached version)
    mcp_servers = {
        "ms365": {
            "command": "npx",
            "args": ["mcp-cache", "npx", "-y", "@batteryho/lokka-cached"],
            "env": {
                "TENANT_ID": settings.MS365_TENANT_ID,
                "CLIENT_ID": settings.MS365_CLIENT_ID,
                "USE_INTERACTIVE": "true"
            }
        }
    }

    system_prompt = """당신은 Outlook 이메일 데이터 수집 전문가입니다.
Lokka MCP (Microsoft 365 MCP)를 사용하여 읽지 않은 이메일 목록을 조회하고, 구조화된 JSON 데이터로 반환해야 합니다.

**작업 지시:**
1. `mcp__ms365__*` 도구를 사용하여 받은편지함의 읽지 않은 이메일을 최신 순으로 최대 10개까지 조회하세요
2. 조회한 이메일들을 **모두 읽음으로 표시**하세요
3. 각 이메일에 대해 다음 정보를 추출하세요:
   - id: 이메일 ID
   - subject: 제목
   - from: 발신자 객체 ({"emailAddress": {"name": "이름", "address": "이메일주소"}} 형식)
   - toRecipients: 수신자 배열
   - ccRecipients: 참조 수신자 배열
   - receivedDateTime: 수신 시간
   - bodyPreview: 본문 미리보기 (200자 이내)
   - isRead: 읽음 여부
   - hasAttachments: 첨부파일 유무

**출력 형식:**
반드시 아래와 같은 JSON 배열 형식으로만 응답하세요. 다른 설명이나 텍스트는 포함하지 마세요:

```json
[
  {
    "id": "메일ID",
    "subject": "제목",
    "from": {
      "emailAddress": {
        "name": "발신자 이름",
        "address": "sender@example.com"
      }
    },
    "toRecipients": [
      {
        "emailAddress": {
          "name": "수신자1",
          "address": "recipient1@example.com"
        }
      }
    ],
    "ccRecipients": [],
    "receivedDateTime": "2024-01-15T10:30:00Z",
    "bodyPreview": "본문 미리보기...",
    "isRead": false,
    "hasAttachments": true
  }
]
```

**주의:** 읽지 않은 이메일이 없으면 빈 배열 [] 반환"""

    try:
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

        async with ClaudeSDKClient(options=options) as client:
            await client.query("mcp__ms365__* 도구를 사용해서 받은편지함의 읽지 않은 이메일을 최신 10개까지 조회하고 JSON으로 반환해주세요.")

            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    result_text = message.result.strip()

                    # JSON 추출 (```json ... ``` 제거)
                    if "```json" in result_text or "```" in result_text:
                        json_start = result_text.find("[")
                        json_end = result_text.rfind("]") + 1
                        if json_start != -1 and json_end > json_start:
                            result_text = result_text[json_start:json_end]

                    emails = json.loads(result_text)
                    logging.info(f"[EMAIL_CHECKER] Fetched {len(emails)} new emails via Lokka MCP")
                    return emails

        return []

    except json.JSONDecodeError as e:
        logging.error(f"[EMAIL_CHECKER] Failed to parse email JSON: {e}")
        return []
    except Exception as e:
        logging.error(f"[EMAIL_CHECKER] Error fetching emails via Lokka MCP: {e}")
        return []


async def process_emails_batch(emails: List[Dict[str, Any]]):
    """
    이메일 배치를 에이전트로 처리

    Args:
        emails: 처리할 이메일 목록
    """
    from app.cc_checkers.ms365.outlook_agent import call_email_task_extractor
    from app.cc_utils.email_tasks_db import get_pending_tasks, complete_task
    from app.queueing_extended import enqueue_message

    if not emails:
        logging.info("[EMAIL_PROCESSOR] No emails to process")
        return

    logging.info(f"[EMAIL_PROCESSOR] Processing {len(emails)} emails...")

    # 로그 출력
    for idx, email in enumerate(emails, 1):
        subject = email.get("subject", "(제목 없음)")
        from_addr = email.get("from", "")
        received_time = email.get("receivedDateTime", "")
        body_preview = email.get("bodyPreview", "")

        logging.info(f"[EMAIL_PROCESSOR] [{idx}/{len(emails)}] From: {from_addr}")
        logging.info(f"[EMAIL_PROCESSOR] [{idx}/{len(emails)}] Subject: {subject}")
        logging.info(f"[EMAIL_PROCESSOR] [{idx}/{len(emails)}] Received: {received_time}")
        logging.info(f"[EMAIL_PROCESSOR] [{idx}/{len(emails)}] Preview: {body_preview[:100]}...")

    # 1. 에이전트 호출하여 이메일 분석 및 할 일 추출 (DB에 저장)
    # 에이전트가 읽음 표시도 같이 처리함
    await call_email_task_extractor(emails)

    # 2. DB에서 Pending 상태인 작업 가져오기
    pending_tasks = get_pending_tasks()

    if not pending_tasks:
        logging.info("[EMAIL_PROCESSOR] No pending tasks found")
        return

    # 3. Slack 채널 큐에 추가
    logging.info(f"[EMAIL_PROCESSOR] Found {len(pending_tasks)} pending tasks")

    for task in pending_tasks:
        task_id = task["id"]
        user_id = task.get("user")
        channel_id = task.get("channel")
        text = task.get("text")

        # Can only add to queue if user, channel, text all exist
        if not user_id or not channel_id or not text:
            logging.warning(f"[EMAIL_PROCESSOR] Task {task_id} missing user/channel/text, skipping")
            continue

        # Add to Slack queue (same pattern as web interface)
        await enqueue_message({
            "text": text,
            "channel": channel_id,
            "ts": "",
            "user": user_id,
            "thread_ts": None,
        })

        # 작업 완료 표시
        complete_task(task_id)
        logging.info(f"[EMAIL_PROCESSOR] Queued task {task_id} to user {user_id}")


async def check_email_updates():
    """
    주기적으로 호출되는 이메일 체크 함수 (스케줄러에서 호출)
    """
    if not settings.MS365_ENABLED:
        logging.warning("[EMAIL_CHECKER] MS365 MCP is not enabled, skipping email check")
        return

    logging.info("[EMAIL_CHECKER] Checking for new emails...")

    try:
        # 새 이메일 조회
        emails = await fetch_new_emails()

        if emails:
            logging.info(f"[EMAIL_CHECKER] Found {len(emails)} new emails, starting background processing")
            # 백그라운드 태스크로 처리
            asyncio.create_task(process_emails_batch(emails))
        else:
            logging.info("[EMAIL_CHECKER] No new emails found")

    except Exception as e:
        logging.error(f"[EMAIL_CHECKER] Error checking emails: {e}")
