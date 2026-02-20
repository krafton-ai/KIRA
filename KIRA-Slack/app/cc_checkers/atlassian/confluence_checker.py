"""
Confluence Checker using Rovo MCP
Rovo MCP를 통해 Confluence 페이지를 모니터링하고 데이터 수집
"""

import asyncio
import logging
import os
from pprint import pprint
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def fetch_recent_pages(hours: int = 1) -> List[Dict[str, Any]]:
    """
    Rovo MCP를 사용하여 최근 업데이트된 Confluence 페이지 조회 (봇 본인이 작성한 글 제외)

    Args:
        hours: 조회할 시간 범위 (기본 1시간)

    Returns:
        최근 업데이트된 페이지 리스트
    """
    if not settings.ATLASSIAN_ENABLED:
        logger.error("[CONFLUENCE_CHECKER] Atlassian MCP is not enabled")
        return []

    # 시간 필터용 cutoff
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M")

    prompt = f"""Confluence 데이터 수집 에이전트입니다.

**작업 지시:**
1. Atlassian MCP 도구로 최근 업데이트된 Confluence 페이지 조회
2. CQL: `lastmodified >= "{cutoff_str}" ORDER BY lastmodified DESC`
3. limit: 10

**출력 형식:**
JSON 배열로만 응답 (설명 없이):
```json
[
  {{
    "id": "123456",
    "title": "Example Page",
    "spaceId": "SPACE",
    "version": {{
      "authorId": "user-id-123",
      "authorEmail": "user@example.com",
      "createdAt": "2024-01-01T00:00:00.000Z"
    }}
  }}
]
```

**주의:** 페이지 없으면 빈 배열 [] 반환"""

    # Atlassian MCP 서버 설정 (remote)
    mcp_servers = {
        "atlassian": {
            "command": "npx",
            "args": ["mcp-cache", "npx", "-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
        }
    }

    options = ClaudeAgentOptions(
        system_prompt=prompt,
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

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query("페이지 목록을 조회하세요.")

            result_message = ""
            async for message in client.receive_response():
                pprint(message)
                if isinstance(message, ResultMessage):
                    result_message = message.result.strip()
                    logger.info(f"[CONFLUENCE_CHECKER] MCP result received: {len(result_message)} chars")
                    break

            if not result_message:
                logger.info("[CONFLUENCE_CHECKER] No result from MCP")
                return []

            # JSON 파싱
            import json

            # ```json ``` 블록 제거
            if "```json" in result_message:
                result_message = result_message.split("```json")[1].split("```")[0].strip()
            elif "```" in result_message:
                result_message = result_message.split("```")[1].split("```")[0].strip()

            pages = json.loads(result_message)

            if not isinstance(pages, list):
                logger.error(f"[CONFLUENCE_CHECKER] Invalid response format: expected list, got {type(pages)}")
                return []

            # Python에서 시간 및 봇 필터링 (Legacy와 동일)
            filtered_pages = []
            for page in pages:
                version = page.get("version", {})
                modified_date_str = version.get("createdAt")
                author_id = version.get("authorId")
                author_email = version.get("authorEmail")

                if modified_date_str:
                    try:
                        # ISO 8601 형식 파싱
                        modified_date = datetime.fromisoformat(modified_date_str.replace('Z', '+00:00'))

                        # 시간 재검증 (MCP가 잘못 필터링했을 수 있음)
                        if modified_date >= cutoff_time:
                            # 봇 본인이 작성한 글 제외 (Legacy와 동일)
                            if author_email and author_email == settings.BOT_EMAIL:
                                logger.info(f"[CONFLUENCE_CHECKER] Skipping page by bot: {page.get('title')}")
                                continue

                            filtered_pages.append(page)
                            logger.debug(f"[CONFLUENCE_CHECKER] Added page: {page.get('title')} by {author_email or author_id}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"[CONFLUENCE_CHECKER] Failed to parse date: {modified_date_str}, error: {e}")
                        continue

            logger.info(f"[CONFLUENCE_CHECKER] Fetched {len(filtered_pages)} pages modified in last {hours} hours (after Python filtering)")
            return filtered_pages

    except json.JSONDecodeError as e:
        logger.error(f"[CONFLUENCE_CHECKER] JSON parsing error: {e}")
        logger.error(f"[CONFLUENCE_CHECKER] Raw result: {result_message[:500]}")
        return []
    except Exception as e:
        logger.error(f"[CONFLUENCE_CHECKER] Error fetching pages: {e}", exc_info=True)
        return []


async def process_pages_batch(pages: List[Dict[str, Any]], chunk_size: int = 5):
    """
    여러 페이지를 배치로 처리 (백그라운드)
    Context overflow 방지를 위해 작은 청크로 나눠서 처리

    Args:
        pages: 페이지 리스트
        chunk_size: 한 번에 처리할 페이지 수 (기본 5개)
    """
    logger.info(f"[CONFLUENCE_PROCESSOR] Processing {len(pages)} pages in background (chunk_size={chunk_size})")

    for idx, page in enumerate(pages, 1):
        page_id = page.get("id", "")
        title = page.get("title", "")

        version = page.get("version", {})
        modified_date = version.get("createdAt", "")
        modified_by = version.get("authorId", "")

        # 페이지 URL 생성
        page_url = f"{settings.ATLASSIAN_CONFLUENCE_SITE_URL}/wiki/spaces/{page.get('spaceId', '')}/pages/{page_id}"

        logger.info(f"[CONFLUENCE_PROCESSOR] [{idx}/{len(pages)}] Title: {title}")
        logger.info(f"[CONFLUENCE_PROCESSOR] [{idx}/{len(pages)}] URL: {page_url}")
        logger.info(f"[CONFLUENCE_PROCESSOR] [{idx}/{len(pages)}] Modified: {modified_date} by {modified_by}")

    # 에이전트 호출하여 중요한 페이지만 요약 (청크 단위로 처리)
    from app.cc_checkers.atlassian.confluence_agent import call_confluence_summarizer, save_to_memory

    # 페이지를 청크로 분할
    chunks = [pages[i:i + chunk_size] for i in range(0, len(pages), chunk_size)]
    logger.info(f"[CONFLUENCE_PROCESSOR] Split into {len(chunks)} chunks")

    all_results = []
    for chunk_idx, chunk in enumerate(chunks, 1):
        logger.info(f"[CONFLUENCE_PROCESSOR] Processing chunk {chunk_idx}/{len(chunks)} ({len(chunk)} pages)")

        result = await call_confluence_summarizer(chunk)

        if result:
            logger.info(f"[CONFLUENCE_PROCESSOR] Chunk {chunk_idx}: Important pages found")
            all_results.append(result)
        else:
            logger.info(f"[CONFLUENCE_PROCESSOR] Chunk {chunk_idx}: No important pages")

    # 모든 청크 결과를 합쳐서 메모리에 저장
    if all_results:
        combined_result = "\n\n---\n\n".join(all_results)
        logger.info(f"[CONFLUENCE_PROCESSOR] Saving {len(all_results)} chunk results to memory")
        await save_to_memory(combined_result)
    else:
        logger.info(f"[CONFLUENCE_PROCESSOR] No important pages to save")

    logger.info(f"[CONFLUENCE_PROCESSOR] Completed processing {len(pages)} pages")


async def check_confluence_updates():
    """
    최근 Confluence 페이지 업데이트 체크 및 배치 처리
    스케줄러에서 주기적으로 호출됨
    """
    if not settings.ATLASSIAN_ENABLED:
        logger.info("[CONFLUENCE_CHECKER] Atlassian MCP is not enabled")
        return

    if not settings.CONFLUENCE_CHECK_ENABLED:
        logger.info("[CONFLUENCE_CHECKER] Confluence check is not enabled")
        return

    logger.info("[CONFLUENCE_CHECKER] Checking recent Confluence updates...")

    try:
        # 최근 시간 이내 업데이트된 페이지 조회
        pages = await fetch_recent_pages(
            hours=settings.CONFLUENCE_CHECK_HOURS or 1
        )

        if pages:
            logger.info(f"[CONFLUENCE_CHECKER] Found {len(pages)} updated pages, starting background processing")
            # 백그라운드 태스크로 처리
            asyncio.create_task(process_pages_batch(pages))
        else:
            logger.info("[CONFLUENCE_CHECKER] No recent page updates found")

    except Exception as e:
        logger.error(f"[CONFLUENCE_CHECKER] Error in check_confluence_updates: {e}", exc_info=True)
