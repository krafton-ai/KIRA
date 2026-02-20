"""
핵심 에이전트 운영 모듈 (Core Agent Operator)

이 모듈은 실제 작업을 수행하는 핵심 에이전트를 실행하고,
도구 사용 전/후 hook을 관리합니다.
"""

import json
import logging
import os

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)

from app.cc_tools.slack.slack_tools import create_slack_mcp_server, get_slack_client
from app.cc_tools.scheduler.scheduler_tools import create_scheduler_mcp_server
from app.cc_tools.x.x_tools import create_x_mcp_server
from app.cc_tools.meeting_transcription.meeting_transcription_tools import (
    create_meetings_mcp_server,
)
from app.cc_tools.deepl.deepl_tools import create_deepl_tools_server
from app.cc_tools.files.files_tools import create_files_mcp_server
from app.config.settings import get_settings, Settings
from app.cc_agents.state_prompt import create_state_prompt


def build_mcp_servers_dict(settings: Settings) -> dict:
    """설정에 따라 활성화된 MCP 서버만 포함하는 딕셔너리를 생성합니다.

    Args:
        settings: Settings 객체

    Returns:
        dict: 활성화된 MCP 서버 딕셔너리
    """
    # 기본 서버들 (항상 포함)
    mcp_servers = {
        "slack": create_slack_mcp_server(),
        "scheduler": create_scheduler_mcp_server(),
        "files": create_files_mcp_server(),
        "time": {"command": "npx", "args": ["-y", "@mcpcentral/mcp-time"]},
        "context7": {"command": "npx", "args": ["-y", "@upstash/context7-mcp"]},
        "arxiv": {
            "command": "npx",
            "args": ["-y", "@langgpt/arxiv-paper-mcp@latest"],
        },
        "airbnb": {
            "command": "npx",
            "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
        },
        "youtube-info": {
            "command": "npx",
            "args": ["-y", "@limecooler/yt-info-mcp"],
        },
        "steam-review": {"command": "npx", "args": ["-y", "steam-review-mcp"]}
    }

    # dev.env 순서대로 조건부 서버들 추가
    # MCP 설정 - Perplexity
    if settings.PERPLEXITY_ENABLED:
        mcp_servers["perplexity"] = {
            "command": "npx",
            "args": ["-y", "server-perplexity-ask"],
            "env": {"PERPLEXITY_API_KEY": settings.PERPLEXITY_API_KEY},
        }

    # MCP 설정 - DeepL
    if settings.DEEPL_ENABLED:
        mcp_servers["deepl"] = create_deepl_tools_server()

    # MCP 설정 - GitHub
    if settings.GITHUB_ENABLED:
        mcp_servers["github"] = {
            "type": "http",
            "url": "https://api.githubcopilot.com/mcp/",
            "headers": {
                "Authorization": f"Bearer {settings.GITHUB_PERSONAL_ACCESS_TOKEN}"
            }
        }

    # MCP 설정 - GitLab
    if settings.GITLAB_ENABLED:
        mcp_servers["gitlab"] = {
            "command": "npx",
            "args": ["mcp-cache", "npx", "-y", "@zereight/mcp-gitlab"],
            "env": {
                "GITLAB_PERSONAL_ACCESS_TOKEN": settings.GITLAB_PERSONAL_ACCESS_TOKEN,
                "GITLAB_API_URL": settings.GITLAB_API_URL,
                "GITLAB_READ_ONLY_MODE": "false",
                "USE_GITLAB_WIKI": "false",
                "USE_MILESTONE": "false",
                "USE_PIPELINE": "false",
            },
        }

    # MCP 설정 - Microsoft 365 (Lokka)
    if settings.MS365_ENABLED:
        mcp_servers["ms365"] = {
            "command": "npx",
            "args": ["mcp-cache", "npx", "-y", "@batteryho/lokka-cached"],
            "env": {
                "TENANT_ID": settings.MS365_TENANT_ID,
                "CLIENT_ID": settings.MS365_CLIENT_ID,
                "USE_INTERACTIVE": "true"
            }
        }

    # MCP 설정 - Atlassian Rovo MCP (Confluence, Jira)
    if settings.ATLASSIAN_ENABLED:
        mcp_servers["atlassian"] = {
            "command": "npx",
            "args": ["mcp-cache", "npx", "-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"],
        }

    # MCP 설정 - TABLEAU MCP
    if settings.TABLEAU_ENABLED:
        mcp_servers["tableau"] = {
            "command": "npx",
            "args": ["mcp-cache", "npx", "-y", "@tableau/mcp-server@latest"],
            "env": {
                "SERVER": settings.TABLEAU_SERVER,
                "SITE_NAME": settings.TABLEAU_SITE_NAME,
                "PAT_NAME": settings.TABLEAU_PAT_NAME,
                "PAT_VALUE": settings.TABLEAU_PAT_VALUE
            }
        }

    # MCP 설정 - X (Twitter)
    if settings.X_ENABLED:
        mcp_servers["x"] = create_x_mcp_server()

    # MCP 설정 - Clova Speech
    if settings.CLOVA_ENABLED:
        mcp_servers["meeting_transcription"] = create_meetings_mcp_server()

    # Computer Use - Chrome
    if settings.CHROME_ENABLED:
        mcp_servers["playwright"] = {
            "command": "npx",
            "args": [
                "mcp-cache",
                "npx",
                "@playwright/mcp@latest",
                "--browser",
                "chrome",
                "--user-data-dir",
                f"{settings.FILESYSTEM_BASE_DIR}/chrome_profile",
                "--caps",
                "vision",
                "--image-responses",
                "allow",
                "--output-dir",
                f"{settings.FILESYSTEM_BASE_DIR}/files/",
            ],
        }

    # MCP 설정 - Custom Remote MCP Servers
    if settings.REMOTE_MCP_SERVERS:
        try:
            remote_servers = json.loads(settings.REMOTE_MCP_SERVERS)
            for server in remote_servers:
                name = server.get("name", "").strip()
                url = server.get("url", "").strip()
                if name and url:
                    mcp_servers[name] = {
                        "command": "npx",
                        "args": ["-y", "mcp-remote", url],
                    }
        except json.JSONDecodeError as e:
            logging.warning(f"[OPERATOR_AGENT] Failed to parse REMOTE_MCP_SERVERS: {e}")

    return mcp_servers


def build_tool_usage_rules(settings: Settings) -> str:
    """설정에 따라 활성화된 도구 사용 원칙만 생성합니다.

    Args:
        settings: Settings 객체

    Returns:
        str: 도구 사용 원칙 문자열
    """
    bot_name = settings.BOT_NAME or "KIRA"

    # 기본 규칙들 (항상 포함)
    rules = f"""## 도구 사용 원칙
<how_to_use_tool>
- 요청을 수행할 때 먼저 `mcp__time__get_current_time`으로 현재 시각을 확인하고, 확인한 시간을 기준으로 정보 탐색에 활용하세요. '어제', '내일', '다음주', '작년', '이번 년도' 같은 상대적 표현은 반드시 확인한 현재 시간 기준으로 정확한 날짜로 변환하여 검색/필터링해야 합니다. 
- `mcp__slack__answer`를 사용할 때는 도구 호출의 결과와 출처, 링크를 최대한 누락되지 않게 상세하게 포함하세요.
- 사용자가 파일을 업로드 하여 slack 파일 url 이 주어졌을 경우, `mcp__slack__download_file_to_channel`를 활용해서 파일을 다운로드하고 작업을 해야합니다.
- `<!subteam^slack_group_id>` 형태는 그룹태그를 의미하며, 이 그룹태그가 입력되는 경우 `mcp__slack__get_usergroup_members` 도구를 호출 후 그룹에 포함된 유저 정보를 읽어온 후에 지시를 수행해야 합니다.
- 보다 긴 대화 맥락이나 스레드 전체의 대화 내용을 참조해야 하는 경우에는 `mcp__slack__get_thread_replies` 도구를 호출하여 데이터를 가져와야 합니다.
- 도구 호출이 3회 이상이면 `mcp__slack__answer_with_emoji`로 작업 상태를 간단히 표현할 수 있습니다.
- 도구 호출이 8회 이상이면 `mcp__slack__answer`로 중간 보고를 할 수 있습니다. 그렇지만 **작업 완료 시에는 반드시 `mcp__slack__answer`로 한 번 더 최종 결과를 응답해야 합니다.** 중간 보고만 하고 끝내지 마세요.
- 다른 사람들에게 메시지를 전달할 때는 `mcp__slack__forward_message`를 사용하세요. 메시지 전달에 대한 응답이 필요하면 `request_answer=True`로 설정하세요.
  - **중복 발송 금지**: 같은 내용의 메시지를 여러 명에게 보낼 때는 `mcp__slack__forward_message`를 **절대 여러 번 호출하지 마세요**. respondents 리스트에 모든 사람을 포함하여 **단 한 번만** 호출해야 합니다.
  - **개인화 금지**: 개인화된 인사말(예: "안녕하세요 OOO님")을 추가하지 마세요. 모든 수신자에게 동일한 메시지를 보내야 합니다.
  - **예외**: 각 사람에게 완전히 다른 내용의 질문을 보낼 때만 각각 별도로 호출하세요.
- `mcp__scheduler__*` 도구의 `text` 파라미터는 **스케줄 실행 시점에 가상 상주 직원이 받을 명령**입니다. 가상 상주 직원에게 내리는 명령 형태로 작성하세요.
  - **명령문 시작**: 반드시 RESPONSE LANGUAGE에 맞춰 작성하세요. (Korean: "{bot_name}님, " / English: "{bot_name}, ")
  - **구체적 작업 포함**: 가상 직원이 실행할 사용자의 명령이 **온전히 모두** 포함되야 합니다. 필요한 링크와 세부 정보를 모두 포함 하세요.
  - **한글 예시**: 사용자 "페이지 요약해줘" → text: "{bot_name}님, https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456 이 페이지 내용을 요약해서 채널에 공지해줘"
  - **영문 예시**: User "summarize the page" → text: "{bot_name}, summarize the content of https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456 and announce it to the channel"
- 워크샵 장소를 찾을 때는 `mcp__airbnb__*` 도구를 사용하세요.
- arXiv 논문 링크(예: https://arxiv.org/)가 주어졌을 때는 `mcp__arxiv__*` 도구를 사용하세요.
- 코드 관련 문서를 찾을 때는 `mcp__context7__*` 도구를 사용하세요.
"""

    # dev.env 순서대로 조건부 규칙들 추가
    conditional_rules = []

    # MCP 설정 - Perplexity
    if settings.PERPLEXITY_ENABLED:
        conditional_rules.append(
            "- 웹 전체에서 정보 검색/종합을 해야하는 경우에는 `mcp__perplexity__*` 도구를 사용하세요. Perplexity 응답에 Citations (출처 링크)가 포함되어 있으면 반드시 답변에 함께 포함하세요."
        )

    # MCP 설정 - DeepL
    if settings.DEEPL_ENABLED:
        conditional_rules.append(
            "- 문서 번역 요청 시 `mcp__deepl__*` 도구를 사용하세요. 바이너리 파일은 Read 툴 사용하지 말고 파일 경로를 바로 전달하세요."
        )

    # MCP 설정 - GitHub
    if settings.GITHUB_ENABLED:
        conditional_rules.append(
            "- GitHub 저장소 작업(이슈, PR, 파일 관리 등)은 `mcp__github__*` 도구를 사용하세요."
        )

    # MCP 설정 - GitLab
    if settings.GITLAB_ENABLED:
        conditional_rules.append(
            "- Gitlab 링크(예: https://gitlab.com/, https://git.company.com/)가 주어졌을 때는 `mcp__gitlab__*` 도구를 사용하세요."
        )

    # MCP - Microsoft 365 (Lokka)
    if settings.MS365_ENABLED:
        conditional_rules.append(
            "- Microsoft 365 작업은 `mcp__ms365__*` 도구를 사용하세요. Outlook 이메일, 캘린더 일정, OneDrive 파일, SharePoint 문서(https://company-my.sharepoint.com/, https://company.sharepoint.com/sites/Team)를 모두 관리할 수 있습니다."
        )

    # MCP - Atlassian
    if settings.ATLASSIAN_ENABLED:
        conditional_rules.append(
            "- Atlassian(Confluence/Jira) 링크(예: https://your-domain.atlassian.net/, https://confluence.company.com/, https://jira.company.com/)가 주어졌을 때는 먼저 `confluence-deep-reader` skill을 사용하고 워크플로우에 따라 `mcp__atlassian__*` 도구를 사용하세요."
        )

    # MCP - Tableau
    if settings.TABLEAU_ENABLED:
        conditional_rules.append(
            "- 테블로 데이터 조회 요청 시 `mcp__tableau__*` 도구를 사용해 데이터를 조회하고 답변하세요. 사용자가 정확한 대시보드를 명시하지 않으면 가장 많이 사용하는 대시보드 1개를 선택해서 보여주세요."
        )

    # MCP 설정 - X (Twitter)
    if settings.X_ENABLED:
        conditional_rules.append(
            "- X 트윗 링크(예: x.com, twitter.com)가 주어졌을 때는 `mcp__x__*` 도구를 사용하세요. 트윗을 게시할 때는 250자 이내로 올려야 합니다."
        )

    # 음성 수신 채널 - Clova (Meeting Transcription)
    if settings.CLOVA_ENABLED:
        conditional_rules.append(
            "- 녹취 회의록, 녹음 회의록 작성 요청 시 `mcp__meeting_transcription__*` 도구를 사용하세요. 먼저 `mcp__meeting_transcription__list_meeting_files`로 날짜별 녹음 파일을 조회하고, `mcp__meeting_transcription__transcribe_meeting`으로 텍스트를 추출하여 회의록을 작성하세요. 날짜 언급이 없다면 가장 최근 파일로 작성하세요."
        )

    # Computer Use - Chrome
    if settings.CHROME_ENABLED:
        conditional_rules.extend([
            "- 특정 사이트에서 여러 게시글이나 콘텐츠를 확인해야하는 경우에는 `web-navigation-strategies` skill을 사용하고 워크플로우에 따라 `mcp__playwright__*` 도구를 사용하세요.",
            "- 회식 장소를 찾을 때는 `mcp__playwright__*` 도구를 사용하세요. 캐치테이블(app.catchtable.co.kr)에서 식당을 검색하고, 네이버에서 각 식당의 블로그 후기 링크를 수집하세요.",
            "- `mcp__playwright__browser_take_screenshot`로 스크린 샷을 저장할 때는 `filename` 파라미터를 `{{channel_id}}/파일명.png` 형태로 지정합니다.",
        ])

    # MCP 설정 - Custom Remote MCP Servers
    if settings.REMOTE_MCP_SERVERS:
        try:
            remote_servers = json.loads(settings.REMOTE_MCP_SERVERS)
            for server in remote_servers:
                name = server.get("name", "").strip()
                instruction = server.get("instruction", "").strip()
                if name and instruction:
                    conditional_rules.append(f"- 다음의 경우에 반드시 `mcp__{name}__*`를 사용하세요: {instruction}")
        except json.JSONDecodeError:
            pass

    # 조건부 규칙들을 기본 규칙에 추가
    if conditional_rules:
        rules += "\n".join(conditional_rules) + "\n"

    rules += "</how_to_use_tool>"

    return rules


async def save_to_memory(
    query: str, final_message: str, slack_data: dict, message_data: dict
) -> None:
    """
    대화 내용을 메모리 큐에 추가합니다.

    Args:
        query: 사용자 질의
        final_message: 최종 답변
        slack_data: Slack API 데이터 (채널, 멤버 정보 포함)
        message_data: 현재 메시지 정보 (user_name, user_id 포함)
    """
    try:
        from app.queueing_extended import enqueue_memory_job

        channel_info = slack_data.get("channel", {})
        channel_id = channel_info.get(
            "channel_id", message_data.get("channel_id", "unknown")
        )
        channel_name = channel_info.get("channel_name", "unknown")
        channel_type = channel_info.get("channel_type", "unknown")

        memory_query = f"""다음은 방금 완료된 Slack 대화 내용입니다. 다음 대화에서 참고할 만한 정보가 있다면 저장하세요.
        
**채널:**
- ID: {channel_id}
- 이름: {channel_name}
- 타입: {channel_type}

**사용자:**
- 이름: {message_data['user_name']}
- ID: {message_data['user_id']}

**요청:**
{query}

**작업 처리 내역:**
{final_message}

`slack-memory-store` skill을 사용해서 이 정보를 적절한 카테고리에 분류하고 저장하세요.
반드시 작업의 성공/실패 사례를 저장하세요.
소속 팀 동료와 관련된 사항은 반드시 저장합니다.
"""

        # 메모리 큐에 작업 추가 (순차 처리됨)
        await enqueue_memory_job({"memory_query": memory_query})
        logging.info(f"[OPERATOR_AGENT] Memory job enqueued")
    except Exception as e:
        logging.error(f"[OPERATOR_AGENT] Memory enqueue failed: {e}")


def create_system_prompt(state_prompt: str) -> str:
    """Core agent를 위한 system prompt 생성

    Args:
        state_prompt: create_state_prompt()로 생성된 현재 상태 프롬프트

    Returns:
        str: 에이전트의 행동 원칙과 도구 사용 원칙을 포함한 system prompt
    """
    # 봇 이름 가져오기
    settings = get_settings()
    bot_name = settings.BOT_NAME or "KIRA"
    bot_role = settings.BOT_ROLE or ""

    # 동적으로 도구 사용 원칙 생성
    tool_usage_rules = build_tool_usage_rules(settings)

    # 직군/역할 섹션 (설정된 경우에만)
    role_section = ""
    if bot_role:
        role_section = f"""

## 회사에서의 역할
<bot_role>
{bot_role}
</bot_role>"""

    system_prompt = f"""당신은 Slack으로 커뮤니케이션 하는 가상 상주 직원 {bot_name}님 입니다.

# 기본 지침
동료들의 요청을 정확하고 효율적으로 처리하여 **Slack 도구**를 통해 응답하고 작업 처리 내역을 정리하세요.
{role_section}

{state_prompt}

## 핵심 행동 원칙
<important_actions>
1. state_data의 "관련 메모리" 섹션을 확인하세요. 전임 에이전트가 요청에 필요한 메모리를 정리했습니다.
2. 반드시 `mcp__slack__answer`도구를 최소 1번 이상 호출합니다.
3. 요청이 불분명하거나 작업이 불가하거나 선택지를 제안할 때도 `mcp__slack__answer`도구로 응답하세요.
4. 작업 실패 시에도 `mcp__slack__answer`로 실패 원인과 대안을 제시하세요.
5. 파일 작업 경로:
   - 영구 보관 파일: FILESYSTEM_BASE_DIR/files/{{channel_id}}/
   - 임시 파일: FILESYSTEM_BASE_DIR/files/{{channel_id}}/tmp/ (작업 완료 후 반드시 삭제)
   - 생성한 파일은 반드시 `mcp__slack__upload_file`로 Slack에 업로드 하세요.
   - 파일 생성 시 한글이 깨지지 않도록 하세요. 텍스트 파일은 `encoding='utf-8'`를 사용하고 PDF는 `pdf` skill의 Korean Font Support 참고하세요.
6. 사용자가 "기억해줘", "저장해줘" 등을 요청하면 긍정적으로 응답하세요. 실제 저장은 다음 메모리 에이전트가 자동으로 처리합니다.
   - 파일과 함께 "갖고 있어줘", "보관해줘" 요청 시: `mcp__slack__download_file_to_channel`로 파일을 다운로드하여 FILESYSTEM_BASE_DIR/files/{{channel_id}}/에 저장하고 확인 메시지로 응답하세요.
7. 동료 요청에 대한 응답은 `mcp__slack__answer`와 `mcp__slack__upload_file`을 사용하세요
   - 텍스트 응답은 `mcp__slack__answer`도구를 사용합니다. 답변이 길 경우, 나눠서 여러번 호출합니다. 중복된 내용으로 여러번 호출하지 않습니다. 파라미터를 state_data에서 가져와 사용합니다.
   - 파일 응답은 `mcp__slack__upload_file`도구를 사용합니다. 파일이 많을 경우, 나눠서 여러번 호출합니다. 파라미터를 state_data에서 가져와 사용합니다.
8. 작업 완료 시, 다음 정보를 포함한 작업 내역을 반환하세요. 메모리에 저장됩니다.:
    - 사용한 도구와 결과 요약
    - 출처와 링크
    - 동료 요청에 대한 응답 내역
</important_actions>

## Skill 사용 원칙
<how_to_use_skill>
1. 반드시 PPT, DOCX, PDF, XLSX 문서를 작업할 때는 `ppt`, `docx`, `pdf`, `xlsx` skill을 사용하세요. 작성자는 특별한 지침이 없으면 "{bot_name}"으로 설정하세요.
2. "기억 정리해줘", "메모리 정리해줘" 등 기억/메모리 정리 요청 시 `slack-memory-cleanup` skill을 사용하세요.
</how_to_use_skill>

{tool_usage_rules}

## 동료 요청에 대한 SLACK 응답 가이드
<slack_answer_guide>
1. You MUST respond in the language specified in "RESPONSE LANGUAGE" section above.
2. 채널과 유저에 대한 답변 지침이 있으면 해당 지침에 따라 응답하세요.
3. 반드시 AI 또는 봇임을 드러내는 표현을 피하세요.
4. 요청과 관련 없는 내용은 응답에 포함하지 마세요.
5. 과도한 이모지를 사용하지 마세요.
6. 반드시 시스템 관련 용어를 자연스러운 일상 표현으로 바꿔 사용하세요. (예: "메모리" → "기억/예전에 들은 거", "파일 경로" → "위치/폴더", "스레드" → "대화", "API 호출" → "확인해봤는데", "버그/에러" → "문제", "디버깅" → "확인 중", "트리거" → "실행")
7. 마크다운 문법(**, ##, -, >, ``` 등)을 사용하지 마세요. 대신 줄바꿈과 들여쓰기로 구조화하세요.
8. 반드시 도구 호출의 결과에 포함된 출처와 링크를 상세히 포함하세요.
9. 반드시 분석은 도구 호출의 결과를 기반으로 하십시오.
10. 어떤 측면에 대해 확신이 없거나 보고서에 필요한 정보가 부족한 경우, 충분한 정보가 없다고 응답하세요.
</slack_answer_guide>

## 가드레일 정책
<guardrails>
**파일 시스템 접근 제한:**
- FILESYSTEM_BASE_DIR 외부의 파일이나 디렉토리에 절대 접근하지 마세요
- 시스템 파일, 홈 디렉토리, 설정 파일 등을 읽거나 수정하는 것은 엄격히 금지됩니다
- 파일 작업은 반드시 FILESYSTEM_BASE_DIR 내부로 제한됩니다

**특정 사이트 읽기 깊이 결정 제한:**
- 특정 사이트의 여러 개의 콘텐츠나 게시글을 읽을 때 읽기 깊이가 불확실한 경우 절대 추론하지 마세요
- 사용자에게 명확히 어떤 수준으로 읽을지 다시 물어보세요
- 잘못된 깊이로 읽어서 시간을 낭비하거나 정보를 놓치는 것은 엄격히 금지됩니다

**Slack 메시지 전송 제한:**
- user_id를 알 수 없거나 불확실한 경우 절대 추론하지 마세요
- 사용자에게 명확히 누구에게 보낼지 다시 물어보거나, 슬랙 태그(@사용자명)를 요청하세요
- 잘못된 user_id로 메시지를 보내는 것은 엄격히 금지됩니다
</guardrails>
"""

    return system_prompt


async def call_operator_agent(
    user_query: str, slack_data: dict, message_data: dict, retrieved_memory: str = ""
) -> None:
    """
    핵심 에이전트를 실행하여 사용자 요청을 처리하고 Slack에 메시지를 전송합니다.

    Args:
        user_query: 사용자 질의 (원본 메시지 텍스트)
        slack_data: Slack API 데이터 (채널, 멤버, 메시지 히스토리)
        message_data: 현재 메시지 정보 (user_id, text, channel_id 등)
        retrieved_memory: 검색된 관련 메모리 내용
    """

    state_prompt = create_state_prompt(slack_data, message_data)

    # 메모리가 있으면 state_prompt에 추가
    if retrieved_memory and retrieved_memory != "관련된 메모리가 없습니다.":
        state_prompt += f"\n\n## 관련 메모리\n<retrieved_memory>\n{retrieved_memory}\n</retrieved_memory>"

    system_prompt = create_system_prompt(state_prompt)

    settings = get_settings()

    # 설정에 따라 활성화된 MCP 서버만 로드
    mcp_servers = build_mcp_servers_dict(settings)

    options = ClaudeAgentOptions(
        mcp_servers=mcp_servers,
        system_prompt=system_prompt,
        model=settings.MODEL_FOR_COMPLEX,
        permission_mode="bypassPermissions",
        allowed_tools=["*"],
        disallowed_tools=[
            "Bash(curl:*)",
            "Read(./.env)",
            "Read(./credential.json)",
            "mcp__tableau__get-view-image",
        ],
        setting_sources=["project"],
        cwd=os.getcwd(),
        max_buffer_size=10 * 1024 * 1024,
    )

    # 세션 아이디 설정
    session_id = None
    final_message = ""
    from devtools import pprint

    # user_query에 역할 선택 지시사항 추가
    enhanced_query = f"""{user_query}

요청을 처리하기 전에 `it-role-expert` skill을 이용해 이 요청에 가장 적합한 IT 역할을 선택하고, 해당 역할의 전문성을 바탕으로 작업을 진행하세요.

'어제', '내일', '다음주', '작년', '이번 년도' 같은 상대적 표현은 반드시 확인한 현재 시간 기준으로 정확한 날짜로 변환하여 검색/필터링해야 합니다."""

    # Context overflow 시 /compact 후 재시도 (같은 client 유지, 최대 2회)
    max_retries = 2

    async with ClaudeSDKClient(options=options) as client:
        for attempt in range(max_retries + 1):
            try:
                # 첫 시도는 새 세션, 재시도는 compact된 세션 이어서
                if session_id:
                    await client.query(enhanced_query, session_id)
                else:
                    await client.query(enhanced_query)

                async for message in client.receive_response():
                    if hasattr(message, "subtype") and message.subtype == "init":
                        session_id = message.data.get("session_id")
                        logging.info(f"[OPERATOR_AGENT] Session ID: {session_id}")

                    pprint(message)

                    if type(message) is ResultMessage:
                        if "API Error" in message.result and "413" in message.result:
                            raise Exception(
                                f"Context overflow in ResultMessage: {message.result}"
                            )

                        final_message = message.result
                        logging.info(
                            f"[OPERATOR_AGENT] Final message received: {final_message[:100]}..."
                        )

                # 최종 메시지가 설정되지 않았을 경우 처리
                if not final_message:
                    final_message = "Unable to generate a response."
                    logging.warning(
                        f"[OPERATOR_AGENT] No final message received, using default"
                    )

                # 성공하면 루프 종료
                break

            except Exception as e:
                error_str = str(e)
                error_msg = error_str.lower()

                is_context_error = any(
                    [
                        "prompt is too long" in error_msg,
                        "context overflow" in error_msg,
                        "413" in error_msg,
                    ]
                )

                if is_context_error and attempt < max_retries:
                    logging.warning(
                        f"[OPERATOR_AGENT] Context overflow detected (attempt {attempt + 1}/{max_retries}), executing /compact..."
                    )

                    # 같은 client로 /compact 실행 (session_id 전달)
                    await client.query("/compact", session_id)
                    async for msg in client.receive_response():
                        if isinstance(msg, ResultMessage):
                            logging.info(f"[OPERATOR_AGENT] /compact executed successfully")
                            break

                    # 같은 client, 원래 query로 재시도
                    continue
                else:
                    # 재시도 횟수 초과 또는 다른 에러
                    logging.error(f"[OPERATOR_AGENT] Error occurred: {e}")
                    if is_context_error:
                        final_message = "The context is too large to process. Please start a new conversation."
                    elif "maximum buffer size" in error_msg:
                        final_message = "The response data is too large to process. Please request a smaller scope."
                    elif not final_message:
                        final_message = "An error occurred while processing the task."

                    # 디버그 모드일 때만 에러 메시지를 Slack으로 전송
                    if settings.DEBUG_SLACK_MESSAGES_ENABLED:
                        try:
                            slack_client = get_slack_client()
                            channel_id = message_data.get("channel_id")
                            thread_ts = message_data.get("thread_ts") or message_data.get("ts")

                            if channel_id:
                                await slack_client.chat_postMessage(
                                    channel=channel_id,
                                    text=f"⚠️ {final_message}",
                                    thread_ts=thread_ts
                                )
                                logging.info(f"[OPERATOR_AGENT] Error message sent to Slack: {final_message}")
                        except Exception as slack_error:
                            logging.error(f"[OPERATOR_AGENT] Failed to send error to Slack: {slack_error}")

                    break

    # Slack에 메시지 전송 (에이전트 레벨로 올림)

    # 메모리에 저장
    await save_to_memory(user_query, final_message, slack_data, message_data)

    return final_message
