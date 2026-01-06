import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from app.config import constant


class Settings(BaseSettings):
    # 공통 환경
    APP_ENV: str = ""

    # AI 모델 설정 (Electron 앱에서 선택 가능, Vertex AI 사용 시 자동 변환)
    MODEL_FOR_SIMPLE: str = "sonnet"     # 판단용 (봇 호출 감지, 분류 등)
    MODEL_FOR_MODERATE: str = "sonnet"   # 분석용 (메모리 관리, 요약 등)
    MODEL_FOR_COMPLEX: str = "sonnet"    # 작업용 (핵심 작업 수행)

    # SLACK 관련
    SLACK_BOT_TOKEN: str = ""
    SLACK_APP_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""
    SLACK_TEAM_ID: str = ""

    # 봇 정보
    BOT_NAME: str = ""
    BOT_EMAIL: str = ""
    BOT_ORGANIZATION: str = ""
    BOT_TEAM: str = ""
    BOT_AUTHORIZED_USERS_EN: str = ""
    BOT_AUTHORIZED_USERS_KR: str = ""
    BOT_ROLE: str = ""
    FILESYSTEM_BASE_DIR: str = ""

    # MCP - Perplexity
    PERPLEXITY_ENABLED: bool = True
    PERPLEXITY_API_KEY: str = ""

    # MCP - DeepL
    DEEPL_ENABLED: bool = True
    DEEPL_API_KEY: str = ""

    # MCP - GitHub
    GITHUB_ENABLED: bool = True
    GITHUB_PERSONAL_ACCESS_TOKEN: str = ""

    # MCP - GitLab
    GITLAB_ENABLED: bool = True
    GITLAB_API_URL: str = ""
    GITLAB_PERSONAL_ACCESS_TOKEN: str = ""

    # MCP - Microsoft 365 (Lokka)
    MS365_ENABLED: bool = False
    MS365_CLIENT_ID: str = ""
    MS365_TENANT_ID: str = ""

    # MCP - Atlassian Rovo
    ATLASSIAN_ENABLED: bool = False
    ATLASSIAN_CONFLUENCE_SITE_URL: str = ""
    ATLASSIAN_CONFLUENCE_DEFAULT_PAGE_ID: str = ""
    ATLASSIAN_JIRA_SITE_URL: str = ""

    # MCP - Tableau
    TABLEAU_ENABLED: bool = False
    TABLEAU_SERVER: str = ""
    TABLEAU_SITE_NAME: str = ""
    TABLEAU_PAT_NAME: str = ""
    TABLEAU_PAT_VALUE: str = ""

    # MCP - X (Twitter)
    X_ENABLED: bool = True
    X_API_KEY: str = ""
    X_API_SECRET: str = ""
    X_ACCESS_TOKEN: str = ""
    X_ACCESS_TOKEN_SECRET: str = ""
    X_OAUTH2_CLIENT_ID: str = ""
    X_OAUTH2_CLIENT_SECRET: str = ""

    # MCP - Clova Speech
    CLOVA_ENABLED: bool = False
    CLOVA_INVOKE_URL: str = ""
    CLOVA_SECRET_KEY: str = ""

    # MCP - Custom Remote MCP Servers (JSON array)
    # Format: [{"name": "server1", "url": "https://...", "instruction": "..."}, ...]
    REMOTE_MCP_SERVERS: str = ""

    # Computer Use
    CHROME_ENABLED: bool = False
    CHROME_ALWAYS_PROFILE_SETUP: bool = False

    # 웹 서버 / 음성 수신 채널
    WEB_INTERFACE_ENABLED: bool = True
    WEB_INTERFACE_AUTH_PROVIDER: str = "microsoft"
    WEB_INTERFACE_URL: str = ""
    WEB_SLACK_CLIENT_ID: str = ""
    WEB_SLACK_CLIENT_SECRET: str = ""
    WEB_MS365_CLIENT_ID: str = ""
    WEB_MS365_CLIENT_SECRET: str = ""
    WEB_MS365_TENANT_ID: str = ""

    # 능동 수신 채널 - Outlook
    OUTLOOK_CHECK_ENABLED: bool = False
    OUTLOOK_CHECK_INTERVAL: int = 5

    # 능동 수신 채널 - Confluence
    CONFLUENCE_CHECK_ENABLED: bool = False
    CONFLUENCE_CHECK_INTERVAL: int = 60
    CONFLUENCE_CHECK_HOURS: int = 1

    # 능동 수신 채널 - Jira
    JIRA_CHECK_ENABLED: bool = False
    JIRA_CHECK_INTERVAL: int = 30

    # 선제적 제안 기능
    DYNAMIC_SUGGESTER_ENABLED: bool = False
    DYNAMIC_SUGGESTER_INTERVAL: int = 15

    # 디버그
    DEBUG_SLACK_MESSAGES_ENABLED: bool = False

    def model_post_init(self, __context):
        load_dotenv("app/config/env/dev.env", override=True)

        # Check for Vertex AI credential
        # 1st priority: User's home directory (~/.kira/) - for internal users
        # 2nd priority: App internal path - for local development
        user_credential_path = os.path.join(
            os.path.expanduser("~"), ".kira", "credential.json"
        )
        dev_credential_path = os.path.join(
            os.path.dirname(__file__), "env", "credential.json"
        )

        credential_path = None
        if os.path.exists(user_credential_path):
            credential_path = user_credential_path
        elif os.path.exists(dev_credential_path):
            credential_path = dev_credential_path

        if credential_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path
            os.environ["ANTHROPIC_VERTEX_PROJECT_ID"] = os.environ.get(
                "ANTHROPIC_VERTEX_PROJECT_ID", "your-project-id"
            )
            os.environ["ANTHROPIC_VERTEX_REGION"] = os.environ.get(
                "ANTHROPIC_VERTEX_REGION", "your-region"
            )
            os.environ["CLAUDE_CODE_USE_VERTEX"] = "1"
            # Pydantic v2 BaseSettings는 frozen이므로 object.__setattr__ 사용
            # 사용자 선택 모델을 Vertex AI 모델명으로 변환
            vertex_model_map = {
                "haiku": "claude-haiku-4-5@20251001",
                "sonnet": "claude-sonnet-4-5@20250929",
                "opus": "claude-opus-4-5@20251101",
            }
            object.__setattr__(self, 'MODEL_FOR_SIMPLE', vertex_model_map.get(self.MODEL_FOR_SIMPLE, self.MODEL_FOR_SIMPLE))
            object.__setattr__(self, 'MODEL_FOR_MODERATE', vertex_model_map.get(self.MODEL_FOR_MODERATE, self.MODEL_FOR_MODERATE))
            object.__setattr__(self, 'MODEL_FOR_COMPLEX', vertex_model_map.get(self.MODEL_FOR_COMPLEX, self.MODEL_FOR_COMPLEX))

@lru_cache
def get_settings() -> Settings:
    run_env: str = os.environ.get("RUN_ENV", constant.DEV)

    setting_config = {}
    env_file_path = f"{constant.ENV_DIR_PATH}/{run_env}.env".replace("..", ".")
    if os.path.exists(env_file_path):
        setting_config["_env_file"] = env_file_path

    settings = Settings(**setting_config)
    return settings
