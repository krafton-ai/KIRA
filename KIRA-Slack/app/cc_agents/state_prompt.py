"""
프롬프트 생성 함수들

이 모듈은 Claude SDK 에이전트에서 사용하는 system prompt와 state prompt를 생성합니다.
"""

import json
import os
from typing import Optional
from app.config.settings import get_settings
from app.cc_utils.language_helper import detect_language


def create_state_prompt(slack_data: Optional[dict] = None, message_data: Optional[dict] = None) -> str:
    """Slack API 데이터와 현재 메시지 정보를 바탕으로 state prompt 생성

    Args:
        slack_data: Slack API로부터 받은 데이터 (채널, 멤버, 최근 메시지 등). None이면 생략됨
        message_data: 현재 메시지 정보 (user_id, text, channel_id, thread_ts 등). None이면 생략됨

    Returns:
        str: 에이전트가 현재 상태를 이해하기 위한 프롬프트
    """
    # 파일 시스템 기본 디렉토리
    settings = get_settings()
    filesystem_base_dir = settings.FILESYSTEM_BASE_DIR or os.getcwd()
    bot_name = settings.BOT_NAME or "봇"
    bot_email = settings.BOT_EMAIL or ""
    bot_organization = settings.BOT_ORGANIZATION or "Your Organization"
    bot_team = settings.BOT_TEAM or ""
    authorized_users_en = settings.BOT_AUTHORIZED_USERS_EN or ""
    authorized_users_kr = settings.BOT_AUTHORIZED_USERS_KR or ""
    confluence_default_page_id = settings.ATLASSIAN_CONFLUENCE_DEFAULT_PAGE_ID or ""

    # combined_data 구성 (None이 아닌 것만 포함)
    combined_data = {
        "filesystem_base_dir": filesystem_base_dir
    }
    if slack_data is not None:
        combined_data["slack_data"] = slack_data
    if message_data is not None:
        combined_data["current_message"] = message_data

    state_json = json.dumps(combined_data, ensure_ascii=False, indent=2)

    # 섹션 구성 (동적 번호 매기기)
    sections = []
    section_num = 0

    # 0. 당신의 정체성 (항상 포함)
    sections.append(f"""### {section_num}. 당신의 정체성
- 이름: {bot_name}
- 이메일: {bot_email}
- 소속 조직: {bot_organization}
- 소속 팀: {bot_team}
- 업무 이해관계자 (영문): {authorized_users_en}
- 업무 이해관계자 (한글): {authorized_users_kr}""")
    section_num += 1

    # 1. slack_data가 있을 때만 채널 정보 추가
    if slack_data is not None:
        sections.append(f"""### {section_num}. 채널 정보 (slack_data):
- `channel`: 현재 채널의 기본 정보 (이름, 타입, 주제, 목적, 멤버 수)
- `members`: 채널에 속한 사용자들의 정보 (user_id, real_name, display_name, email)
- `recent_messages`: 최근 대화 내역 ("[사용자명]: 메시지 내용" 형식)""")
        section_num += 1

    # 2. message_data가 있을 때만 현재 메시지 추가
    if message_data is not None:
        sections.append(f"""### {section_num}. 현재 메시지 (current_message):
- `user_id`: 메시지를 보낸 사용자의 Slack ID
- `user_text`: 사용자가 보낸 메시지 내용
- `channel_id`: 메시지가 발생한 채널 ID
- `thread_ts`: 스레드 내 메시지인 경우에만 값 존재
- `message_ts`: 이 메시지의 타임스탬프
- `files`: 첨부된 파일 정보 (존재하는 경우). 파일명, URL, MIME 타입 등이 포함됩니다.""")
        section_num += 1

    # 3. 파일 시스템 정보 (항상 포함)
    sections.append(f"""### {section_num}. 파일 시스템 정보 (FILESYSTEM_BASE_DIR):
- 이 디렉토리는 파일을 생성하거나 저장할 때 사용하는 기본 경로입니다.
- 파일 작업 시 이 경로를 기준으로 하위 폴더를 만들어 사용하세요.""")
    section_num += 1

    # 4. Confluence 기본 페이지 (설정되어 있을 때만)
    if confluence_default_page_id:
        sections.append(f"""### {section_num}. Confluence 기본 페이지:
- 사용자가 "위키에 올려줘", "Confluence에 작성해줘" 등으로 요청하면 페이지 ID `{confluence_default_page_id}`를 사용하세요.
- 명시적으로 다른 페이지를 지정하지 않는 한, 이 페이지의 하위 페이지를 만들어 작성합니다.""")
        section_num += 1

    # 5. 응답 언어 감지
    user_text = message_data.get("user_text", "") if message_data else ""
    response_language = detect_language(user_text)

    state_prompt = f"""
## RESPONSE LANGUAGE
You MUST respond in {response_language}. This is a critical requirement.

## 작업을 수행하기 위한 상태 정보:
<state_data>
{chr(10).join(sections)}

{state_json}
</state_data>""".strip()

    return state_prompt



