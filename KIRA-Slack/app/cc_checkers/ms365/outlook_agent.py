"""
이메일 요약 에이전트 (Email Summarizer)

여러 이메일을 분석하여 중요한 정보만 추출하고 요약합니다.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from app.cc_agents.memory_retriever.agent import call_memory_retriever
from app.cc_tools.email_tasks import create_email_tasks_mcp_server
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)


def create_system_prompt(state_prompt: str, bot_name: str) -> str:
    """Email task extractor를 위한 system prompt 생성

    Args:
        state_prompt: create_state_prompt()로 생성된 현재 상태 프롬프트
        bot_name: 봇 이름

    Returns:
        str: 에이전트의 행동 원칙과 도구 사용 원칙을 포함한 system prompt
    """
    system_prompt = f"""당신은 Slack으로 커뮤니케이션 하는 가상 상주 직원 {bot_name}님 입니다.

# 기본 지침
전달받은 이메일들을 분석하여 **당신에게 할당된 할 일**을 추출하고 DB에 저장하세요.

{state_prompt}

## 핵심 행동 원칙
<important_actions>
1. 전달받은 이메일들을 분석하여 당신에게 할당된 액션 아이템을 추출합니다.
2. 필요시 이메일 전체 본문을 조회합니다.
3. 액션 아이템이 있으면 `mcp__email_tasks__add_email_task`로 DB에 저장합니다.
4. 처리 결과를 요약하여 출력합니다.
</important_actions>

## 도구 사용 원칙
<how_to_use_tool>
1. 미리보기로 판단이 어려우면 이메일 전체 본문을 조회해야 합니다.
2. 담당자의 user_id, user_name, channel_id는 retrieved_memory에서 찾아야 합니다.
3. `mcp__email_tasks__add_email_task`의 `text` 파라미터는 반드시 "{bot_name}님, "으로 시작해야 하며, 이메일 원문 언어로 작성해야 합니다.
   - 한글 예: "{bot_name}님, 김철수님이 보낸 '문서 검토 요청'에 대해 설계 문서를 검토하고 피드백을 제출해주세요."
   - 영문 예: "{bot_name}, please review the design document and submit feedback regarding 'Document Review Request' sent by John Smith."
4. 반드시 1개의 이메일에 여러 할 일이 있으면 각각 **별도로** 저장해야 합니다.
5. user_id, user_name, channel_id를 모두 찾지 못하면 해당 할 일은 저장하지 않습니다.
6. 파일을 만들어야 할 경우 반드시 `FILESYSTEM_BASE_DIR/checkers/tmp/` 디렉토리에 임시로 생성하고, 작업 완료 후 삭제하세요.
</how_to_use_tool>

## 가드레일 정책
<guardrails>
**파일 시스템 접근 제한:**
- FILESYSTEM_BASE_DIR 외부의 파일이나 디렉토리에 절대 접근하지 마세요
- 시스템 파일, 홈 디렉토리, 설정 파일 등을 읽거나 수정하는 것은 엄격히 금지됩니다
- 파일 작업은 반드시 FILESYSTEM_BASE_DIR 내부로 제한됩니다
</guardrails>"""

    return system_prompt


async def call_email_task_extractor(
    emails: List[Dict[str, Any]]
) -> Optional[str]:
    """
    이메일 배치를 분석하여 할 일을 추출하고 DB에 저장합니다.

    Args:
        emails: 이메일 리스트 (from, subject, body, receivedDateTime 포함)

    Returns:
        Optional[str]: 처리 결과 요약 (할 일이 없으면 None)
    """
    if not emails:
        return None

    # 이메일 리스트를 텍스트로 변환
    emails_text = ""
    for idx, email in enumerate(emails, 1):
        email_id = email.get("id", "")
        from_info = email.get("from", {}).get("emailAddress", {})
        from_name = from_info.get("name", "Unknown")
        from_address = from_info.get("address", "")
        subject = email.get("subject", "")
        body_preview = email.get("bodyPreview", "")
        received_time = email.get("receivedDateTime", "")
        has_attachments = email.get("hasAttachments", False)

        # 수신자 정보 추출
        to_recipients = email.get("toRecipients", [])
        to_list = [f"{r.get('emailAddress', {}).get('name', '')} <{r.get('emailAddress', {}).get('address', '')}>" for r in to_recipients]
        to_text = ", ".join(to_list) if to_list else "없음"

        # 참조 수신자 정보 추출
        cc_recipients = email.get("ccRecipients", [])
        cc_list = [f"{r.get('emailAddress', {}).get('name', '')} <{r.get('emailAddress', {}).get('address', '')}>" for r in cc_recipients]
        cc_text = ", ".join(cc_list) if cc_list else "없음"

        emails_text += f"""
이메일 {idx}:
이메일 ID: {email_id}
발신자: {from_name} <{from_address}>
수신자: {to_text}
참조(CC): {cc_text}
제목: {subject}
수신 시간: {received_time}
첨부파일: {"있음" if has_attachments else "없음"}
본문 미리보기:
{body_preview}

---
"""

    # settings와 bot_name 먼저 가져오기
    from app.cc_agents.state_prompt import create_state_prompt
    from app.config.settings import get_settings

    settings = get_settings()
    bot_name = settings.BOT_NAME or "봇"

    email_task_memory_query = f"""다음 {len(emails)}개의 이메일에서 발신자의 정보와 관련된 모든 사람의 정보를 찾아 메모리를 취합해 알려주세요.
반드시 해당 채널과 요청 유저에 대한 **지침**과 정보(channel_id, user_id, user_name)를 포함하세요.

{emails_text}"""

    # 1. 메모리 검색 (email task extractor 용)
    retrieved_memory = await call_memory_retriever(
        email_task_memory_query
    )
    logging.info(f"[EMAIL_TASK_EXTRACTOR] Memory retrieved: {retrieved_memory[:100] if retrieved_memory else 'None'}...")

    state_prompt = create_state_prompt()

    # 메모리 추가
    state_prompt += f"\n\n## 관련 메모리\n<retrieved_memory>\n{retrieved_memory}\n</retrieved_memory>"

    system_prompt = create_system_prompt(state_prompt, bot_name)

    # 2. email task extractor 호출
    query = f"""다음 {len(emails)}개의 이메일에서 당신({bot_name})에게 할당된 할 일을 추출하여 DB에 저장하세요.

`email-action-extractor` skill을 이용해 액션 아이템을 추출하세요.

{emails_text}"""

    # Lokka MCP 서버 설정 (cached version)
    mcp_servers = {
        "ms365": {
            "command": "npx",
            "args": ["mcp-cache", "npx", "-y", "@batteryho/lokka-cached"],
            "env": {
                "TENANT_ID": settings.MS365_TENANT_ID,
                "CLIENT_ID": settings.MS365_CLIENT_ID,
                "USE_INTERACTIVE": "true"
            }
        },
        "email_tasks": create_email_tasks_mcp_server()
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
        mcp_servers=mcp_servers
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(query)

            result_message = ""
            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    result_message = message.result.strip()
                    logging.info(f"[EMAIL_TASK_EXTRACTOR] Result: {result_message[:100]}...")
                    break

            # 할 일이 없으면 None 반환
            if not result_message or ("할 일" in result_message and "없" in result_message):
                logging.info("[EMAIL_TASK_EXTRACTOR] No tasks extracted")
                return None

            return result_message

    except Exception as e:
        logging.error(f"[EMAIL_TASK_EXTRACTOR] Error: {e}")
        return None
