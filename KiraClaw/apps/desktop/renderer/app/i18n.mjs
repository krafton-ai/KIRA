const STORAGE_KEY = "kiraclaw-language";

const translations = {
  en: {
    app: {
      title: "KiraClaw",
    },
    nav: {
      home: "Home",
      talk: "Talk",
      channels: "Channels",
      schedules: "Schedules",
      settings: "Settings",
      logs: "Logs",
    },
    common: {
      online: "Online",
      offline: "Offline",
      checking: "Checking",
      reload: "Reload",
      saveChannel: "Save Channel",
      saveMcp: "Save MCP",
      saveSettings: "Save Settings",
      saveAndRestartEngine: "Save And Restart Engine",
      startEngine: "Start Engine",
      restart: "Restart",
      stop: "Stop",
      readOnly: "Read Only",
      loadedOnDemand: "Loaded On Demand",
      activeCount: "{{count}} Active",
      later: "Later",
      openFolder: "Open Folder",
      openProfileSetup: "Open Profile Setup",
      openWorkspaceFolder: "Open Workspace Folder",
      openLogFile: "Open Log File",
      enabled: "Enabled",
      disabled: "Disabled",
      name: "Name",
      url: "URL",
      delete: "Delete",
      addServer: "+ Add Server",
      viewDetails: "View Details",
      none: "None",
      toggleSecretVisibility: "Toggle secret visibility",
    },
    home: {
      daemonBadge: "KIRA Engine offline",
      myNameIs: "My name is {{name}}",
      starting: "Starting...",
      restarting: "Restarting...",
      stopping: "Stopping...",
      onlineMessage: "KIRA Engine is online on this device.",
      offlineMessage: "KIRA Engine is offline on this device.",
      checkingMessage: "Checking KIRA Engine status...",
    },
    chat: {
      title: "Talk",
      subtitle: "Talk directly with the same KIRA Engine used by Slack.",
      session: "Session",
      clear: "Clear",
      ready: "Direct chat is ready.",
      placeholder: "Ask KIRA to work on something.",
      send: "Send",
      thinking: "Thinking...",
      thinkingLabel: "Thinking",
      preparingResponse: "Preparing a response...",
      spokenReply: "Spoken reply",
      internalSummary: "Internal summary",
      usedTools: "Used",
      startEngineFirst: "Start the KIRA Engine first.",
      runFailed: "Run failed: {{message}}",
      userLabel: "You",
      emptyInternalSummary: "(empty internal summary)",
    },
    channels: {
      title: "Channels",
      subtitle: "Desktop chat, Slack, and lightweight chat channels can share the same local engine.",
      availableNow: "Available now",
      slackDesc: "Desktop chat and Slack already share the same KIRA Engine.",
      telegramDesc: "Telegram can use the same local engine through a lightweight bot adapter.",
      discordDesc: "Discord can use the same local engine for DMs and server channels through a bot gateway.",
      moreChannels: "More channels",
      moreChannelsDesc: "Additional channels will be added here after the core Slack flow is solid.",
      slackTitle: "Slack",
      slackCopy: "These values let Slack talk to the same local engine that desktop chat uses.",
      telegramTitle: "Telegram",
      telegramCopy: "Telegram uses a simple bot token and currently works best for direct chats with the same local engine.",
      discordTitle: "Discord",
      discordCopy: "Discord uses a bot token and can share the same local engine for direct messages and server channels.",
      slackBotToken: "Slack Bot Token",
      slackAppToken: "Slack App Token",
      slackSigningSecret: "Slack Signing Secret",
      slackTeamId: "Slack Team ID",
      allowedNames: "Allowed Names",
      telegramBotToken: "Telegram Bot Token",
      discordBotToken: "Discord Bot Token",
      statusReadFrom: "Channel settings are read from `~/.kira/config.env`.",
    },
    mcp: {
      subtitle: "Optional retrieval and integration MCP servers live here.",
      slackRetrieveTitle: "Slack Retrieve",
      slackRetrieveDesc: "Use Slack Retrieve with a separate user token for workspace-wide search and history lookup. Keep current-conversation replies and delivery in Channels > Slack.",
      slackRetrieveClientId: "Slack Retrieve Client ID",
      slackRetrieveClientSecret: "Slack Retrieve Client Secret",
      slackRetrieveRedirectUri: "Redirect URL",
      connectSlack: "Connect Slack",
      slackRetrieveEngineRequired: "Start the KIRA Engine before connecting Slack Retrieve.",
      browserTitle: "Browser",
      browserDesc: "Chrome profile setup happens before the engine starts. The profile lives inside your configured workspace folder as `chrome_profile`.",
      browserSetupCopy: "Use this before browser MCP tasks to sign in with the same Chrome profile.",
      perplexityDesc: "Use the npm MCP package with your Perplexity API key.",
      gitlabDesc: "Use the npm GitLab MCP package. `https://gitlab.com` is enough for GitLab.com.",
      ms365Desc: "Lokka MCP uses interactive OAuth on first run and covers Outlook, OneDrive, and SharePoint.",
      atlassianDesc: "Remote Atlassian MCP uses browser OAuth on first run. Use one of the site URLs to scope the tenant.",
      tableauDesc: "Tableau MCP uses server, site, and PAT values from your Tableau account.",
      customRemoteTitle: "Custom Remote MCP",
      customRemoteDesc: "Add remote MCP servers with a name and URL. They will load through `mcp-remote`.",
      perplexityApiKey: "Perplexity API Key",
      gitlabUrl: "GitLab URL",
      accessToken: "Access Token",
      clientId: "Client ID",
      tenantId: "Tenant ID",
      confluenceSiteUrl: "Confluence Site URL",
      jiraSiteUrl: "Jira Site URL",
      defaultConfluencePageId: "Default Confluence Page ID",
      server: "Server",
      siteName: "Site Name",
      patName: "PAT Name",
      patValue: "PAT Value",
      noRemoteServers: "No custom remote MCP servers yet.",
      customNameRequired: "Custom MCP name is required.",
      customNamePattern: "Custom MCP name can use only lowercase letters, numbers, and hyphens.",
      customUrlRequired: "Custom MCP URL is required for {{name}}.",
      customNameDuplicated: "Custom MCP name is duplicated: {{name}}.",
      enabledInConfig: "Enabled in config: {{names}}",
      loadedNow: "Loaded now: {{names}}",
      failed: "Failed: {{names}}",
      settingsReadFrom: "MCP settings are read from ~/.kira/config.env.",
      noOptionalLoaded: "No optional MCP integrations are loaded right now.",
      browserEnabledLabel: "Enabled",
      statusSave: "Save MCP",
    },
    schedules: {
      title: "Schedules",
      subtitle: "View the registered scheduler jobs stored in the current workspace.",
      registered: "Registered schedules",
      loading: "Loading schedules...",
      loadFailedTitle: "Schedule load failed",
      noSchedulesTitle: "No schedules yet",
      noSchedulesBody: "No registered schedules were found in the current workspace.",
      noSchedulesConfigured: "No schedules are configured yet.",
      unknownSchedule: "Unknown schedule",
      oneTime: "One time",
      noPromptText: "No prompt text.",
      scheduleLabel: "Schedule",
      userLabel: "User {{user}}",
      loadFailed: "Schedule load failed: {{message}}",
      loadedCount: "{{count}} schedule{{suffix}} loaded{{fileSuffix}}.",
    },
    skills: {
      title: "Skills",
      subtitle: "See which SKILL.md packages KiraClaw can load from the workspace folders.",
      available: "Available Skills",
      status: "Skills are discovered from the workspace folders.",
      noSkillsTitle: "No skills found",
      noSkillsBody: "Put skill folders under the workspace skills directory.",
      noDescription: "No description.",
      availableCount: "{{count}} skill{{suffix}} available.",
    },
    logs: {
      title: "Logs",
      subtitle: "Inspect recent internal summaries, spoken replies, tool usage, and silent runs.",
      recent: "Recent logs",
      loading: "Loading recent runs...",
      loadFailedTitle: "Run log load failed",
      noLogsTitle: "No logs yet",
      noLogsBody: "No recent logs have been recorded yet.",
      prompt: "Prompt",
      internalSummary: "Internal Summary",
      spokenReply: "Spoken Reply",
      tools: "Tools",
      silentReason: "Silent Reason",
      error: "Error",
      loadFailed: "Run log load failed: {{message}}",
      noRecentLogs: "No recent logs yet.",
      noRecentLogsWithFile: "No recent logs yet · {{path}}",
      recentCount: "{{count}} recent log{{suffix}}{{fileSuffix}}.",
      unknownSource: "unknown",
      runLabel: "run",
      unknownState: "unknown",
    },
    settings: {
      title: "Settings",
      subtitle: "Configure the KIRA Engine, Slack adapter, and model keys in one place.",
      language: "Language",
      theme: "Theme",
      themeRed: "Krafton Red",
      themePubg: "PUBG Gold",
      identityTitle: "Identity",
      identityDesc: "Choose the name this desktop agent shows inside the app and Slack.",
      agentName: "Agent Name",
      persona: "Persona",
      modelTitle: "Model",
      modelDesc: "Pick the provider the engine should use and register the keys it needs.",
      provider: "Provider",
      modelOverride: "Model Override",
      personaPlaceholder: "Calm, concise, pragmatic. Prefer action over explanation. Speak only when useful in group spaces.",
      anthropicApiKey: "Anthropic API Key",
      openaiApiKey: "OpenAI API Key",
      workspaceTitle: "Workspace",
      workspaceDesc: "Keep the bridge mode simple: reuse `.kira` and choose the workspace this agent should use.",
      filesystemBaseDir: "Filesystem Base Dir",
      statusReadFrom: "Settings are read from `~/.kira/config.env`.",
    },
    status: {
      savingSettings: "Saving settings...",
      restartingWithNewSettings: "Restarting KIRA Engine with the new settings...",
      engineRestartedWithNewSettings: "KIRA Engine restarted with the new settings.",
      engineRestartFailed: "KIRA Engine restart failed.",
      settingsSavedAndRestarted: "Settings saved and engine restarted.",
      settingsSavedButRestartFailed: "Settings saved, but engine restart failed.",
      settingsSavedToConfig: "Settings saved to ~/.kira/config.env.",
      saveFailed: "Save failed: {{message}}",
      actionProgress: "{{action}} KIRA Engine...",
      actionCompleted: "KIRA Engine {{action}} completed.",
      actionFailed: "KIRA Engine {{action}} failed: {{message}}",
      openingChromeProfileSetup: "Opening Chrome profile setup...",
      chromeProfileSetupOpened: "Chrome profile setup opened.",
      profileSetupFailed: "Profile setup failed: {{message}}",
      filesystemBaseDirEmpty: "Filesystem Base Dir is empty.",
      openingFilesystemBaseDir: "Opening Filesystem Base Dir...",
      filesystemBaseDirOpened: "Filesystem Base Dir opened.",
      skillFolderNotConfigured: "Skill folder is not configured.",
      openingSkillFolder: "Opening skill folder...",
      skillFolderOpened: "Skill folder opened.",
      runLogFileNotConfigured: "Run log file is not configured.",
      openingRunLogFile: "Opening run log file...",
      runLogFileOpened: "Run log file opened.",
      openFolderFailed: "Open Folder failed: {{message}}",
      skillLoadFailed: "Skill load failed: {{message}}",
      slackRetrieveClientCredentialsRequired: "Slack Retrieve Client ID and Client Secret are required.",
      slackRetrieveStartEngineFirst: "Start the KIRA Engine before connecting Slack Retrieve.",
      slackRetrieveOauthStarted: "Slack authorization started.",
      slackRetrieveOauthRestarting: "Slack connected. Restarting KIRA Engine...",
      slackRetrieveOauthRestarted: "KIRA Engine restarted with the new Slack Retrieve token.",
      start: "Starting",
      restart: "Restarting",
      stop: "Stopping",
      updating: "Updating",
    },
  },
  ko: {
    app: {
      title: "KiraClaw",
    },
    nav: {
      home: "홈",
      talk: "대화",
      channels: "채널",
      schedules: "스케줄",
      settings: "설정",
      logs: "로그",
    },
    common: {
      online: "온라인",
      offline: "오프라인",
      checking: "확인 중",
      reload: "새로고침",
      saveChannel: "채널 저장",
      saveMcp: "MCP 저장",
      saveSettings: "설정 저장",
      saveAndRestartEngine: "저장 후 엔진 재시작",
      startEngine: "엔진 시작",
      restart: "재시작",
      stop: "중지",
      readOnly: "읽기 전용",
      loadedOnDemand: "필요 시 로드",
      activeCount: "{{count}}개 활성",
      later: "나중에",
      openFolder: "폴더 열기",
      openProfileSetup: "프로필 설정 열기",
      openWorkspaceFolder: "워크스페이스 폴더 열기",
      openLogFile: "로그 파일 열기",
      enabled: "활성화",
      disabled: "비활성화",
      name: "이름",
      url: "URL",
      delete: "삭제",
      addServer: "+ 서버 추가",
      viewDetails: "상세 보기",
      none: "없음",
      toggleSecretVisibility: "비밀값 표시 전환",
    },
    home: {
      daemonBadge: "KIRA 엔진 오프라인",
      myNameIs: "내 이름은 {{name}}",
      starting: "시작 중...",
      restarting: "재시작 중...",
      stopping: "중지 중...",
      onlineMessage: "이 기기에서 KIRA 엔진이 실행 중입니다.",
      offlineMessage: "이 기기에서 KIRA 엔진이 꺼져 있습니다.",
      checkingMessage: "KIRA 엔진 상태를 확인하는 중입니다...",
    },
    chat: {
      title: "대화",
      subtitle: "Slack과 같은 KIRA 엔진으로 바로 대화합니다.",
      session: "세션",
      clear: "비우기",
      ready: "직접 대화할 준비가 됐습니다.",
      placeholder: "KIRA에게 작업을 요청해 보세요.",
      send: "보내기",
      thinking: "생각 중...",
      thinkingLabel: "Thinking",
      preparingResponse: "응답을 준비하는 중...",
      spokenReply: "실제 발화",
      internalSummary: "내부 요약",
      usedTools: "사용 도구",
      startEngineFirst: "먼저 KIRA 엔진을 시작하세요.",
      runFailed: "실행 실패: {{message}}",
      userLabel: "나",
      emptyInternalSummary: "(내부 요약 없음)",
    },
    channels: {
      title: "채널",
      subtitle: "데스크톱 대화, Slack, 경량 채널이 같은 로컬 엔진을 공유할 수 있습니다.",
      availableNow: "현재 사용 가능",
      slackDesc: "데스크톱 대화와 Slack은 이미 같은 KIRA 엔진을 공유합니다.",
      telegramDesc: "Telegram은 가벼운 봇 어댑터를 통해 같은 로컬 엔진을 사용할 수 있습니다.",
      discordDesc: "Discord는 봇 게이트웨이로 DM과 서버 채널에서 같은 로컬 엔진을 사용할 수 있습니다.",
      moreChannels: "추가 채널",
      moreChannelsDesc: "핵심 Slack 흐름이 안정되면 여기에 채널이 더 추가됩니다.",
      slackTitle: "Slack",
      slackCopy: "이 값들은 Slack이 데스크톱 대화와 같은 로컬 엔진을 사용하도록 합니다.",
      telegramTitle: "Telegram",
      telegramCopy: "Telegram은 단순한 봇 토큰을 사용하며 현재는 같은 로컬 엔진으로 1:1 대화에 가장 잘 맞습니다.",
      discordTitle: "Discord",
      discordCopy: "Discord는 봇 토큰을 사용하며 DM과 서버 채널에서 같은 로컬 엔진을 공유할 수 있습니다.",
      slackBotToken: "Slack 봇 토큰",
      slackAppToken: "Slack 앱 토큰",
      slackSigningSecret: "Slack 서명 시크릿",
      slackTeamId: "Slack 팀 ID",
      allowedNames: "허용 이름",
      telegramBotToken: "Telegram 봇 토큰",
      discordBotToken: "Discord 봇 토큰",
      statusReadFrom: "채널 설정은 `~/.kira/config.env`에서 읽습니다.",
    },
    mcp: {
      subtitle: "선택형 조회 및 연동 MCP 서버를 여기에서 관리합니다.",
      slackRetrieveTitle: "Slack Retrieve",
      slackRetrieveDesc: "Slack Retrieve는 별도 user token으로 워크스페이스 전체 검색과 기록 조회에만 사용합니다. 현재 대화에서 답하거나 전달하는 Slack 연결은 채널 > Slack에 그대로 두세요.",
      slackRetrieveClientId: "Slack Retrieve Client ID",
      slackRetrieveClientSecret: "Slack Retrieve Client Secret",
      slackRetrieveRedirectUri: "Redirect URL",
      connectSlack: "Slack 연결",
      slackRetrieveEngineRequired: "Slack Retrieve를 연결하기 전에 KIRA 엔진을 먼저 시작하세요.",
      browserTitle: "브라우저",
      browserDesc: "Chrome 프로필 설정은 엔진 시작 전에 진행됩니다. 프로필은 워크스페이스 폴더 안의 `chrome_profile`에 저장됩니다.",
      browserSetupCopy: "브라우저 MCP 작업 전, 같은 Chrome 프로필로 로그인하려면 이 버튼을 사용하세요.",
      perplexityDesc: "Perplexity API 키와 함께 npm MCP 패키지를 사용합니다.",
      gitlabDesc: "npm GitLab MCP 패키지를 사용합니다. GitLab.com이면 `https://gitlab.com`만으로 충분합니다.",
      ms365Desc: "Lokka MCP는 첫 실행 시 대화형 OAuth를 사용하며 Outlook, OneDrive, SharePoint를 다룹니다.",
      atlassianDesc: "원격 Atlassian MCP는 첫 실행 시 브라우저 OAuth를 사용합니다. 사이트 URL 중 하나로 테넌트를 지정하세요.",
      tableauDesc: "Tableau MCP는 Tableau 계정의 서버, 사이트, PAT 값을 사용합니다.",
      customRemoteTitle: "커스텀 원격 MCP",
      customRemoteDesc: "이름과 URL로 원격 MCP 서버를 추가합니다. 내부적으로 `mcp-remote`로 로드됩니다.",
      perplexityApiKey: "Perplexity API 키",
      gitlabUrl: "GitLab URL",
      accessToken: "액세스 토큰",
      clientId: "클라이언트 ID",
      tenantId: "테넌트 ID",
      confluenceSiteUrl: "Confluence 사이트 URL",
      jiraSiteUrl: "Jira 사이트 URL",
      defaultConfluencePageId: "기본 Confluence 페이지 ID",
      server: "서버",
      siteName: "사이트 이름",
      patName: "PAT 이름",
      patValue: "PAT 값",
      noRemoteServers: "아직 커스텀 원격 MCP 서버가 없습니다.",
      customNameRequired: "커스텀 MCP 이름이 필요합니다.",
      customNamePattern: "커스텀 MCP 이름은 소문자, 숫자, 하이픈만 사용할 수 있습니다.",
      customUrlRequired: "{{name}}용 커스텀 MCP URL이 필요합니다.",
      customNameDuplicated: "중복된 커스텀 MCP 이름입니다: {{name}}.",
      enabledInConfig: "설정에서 활성화됨: {{names}}",
      loadedNow: "현재 로드됨: {{names}}",
      failed: "실패: {{names}}",
      settingsReadFrom: "MCP 설정은 ~/.kira/config.env에서 읽습니다.",
      noOptionalLoaded: "현재 로드된 선택형 MCP 연동이 없습니다.",
      browserEnabledLabel: "활성화",
      statusSave: "MCP 저장",
    },
    schedules: {
      title: "스케줄",
      subtitle: "현재 워크스페이스에 저장된 스케줄러 작업을 봅니다.",
      registered: "등록된 스케줄",
      loading: "스케줄 불러오는 중...",
      loadFailedTitle: "스케줄 로드 실패",
      noSchedulesTitle: "스케줄이 없습니다",
      noSchedulesBody: "현재 워크스페이스에서 등록된 스케줄을 찾지 못했습니다.",
      noSchedulesConfigured: "설정된 스케줄이 없습니다.",
      unknownSchedule: "알 수 없는 스케줄",
      oneTime: "1회 실행",
      noPromptText: "프롬프트가 없습니다.",
      scheduleLabel: "스케줄",
      userLabel: "사용자 {{user}}",
      loadFailed: "스케줄 로드 실패: {{message}}",
      loadedCount: "스케줄 {{count}}개 로드됨{{fileSuffix}}.",
    },
    skills: {
      title: "Skills",
      subtitle: "KiraClaw가 워크스페이스 폴더에서 불러올 수 있는 SKILL.md 패키지를 확인합니다.",
      available: "사용 가능한 Skills",
      status: "Skills는 워크스페이스 폴더에서 자동 탐색됩니다.",
      noSkillsTitle: "스킬이 없습니다",
      noSkillsBody: "워크스페이스 skills 디렉터리 아래에 스킬 폴더를 넣어 주세요.",
      noDescription: "설명 없음.",
      availableCount: "사용 가능한 스킬 {{count}}개.",
    },
    logs: {
      title: "로그",
      subtitle: "최근 내부 요약, 실제 발화, 도구 사용, 무응답 실행을 확인합니다.",
      recent: "최근 로그",
      loading: "최근 실행 로그를 불러오는 중...",
      loadFailedTitle: "실행 로그 로드 실패",
      noLogsTitle: "로그가 없습니다",
      noLogsBody: "아직 기록된 최근 로그가 없습니다.",
      prompt: "프롬프트",
      internalSummary: "내부 요약",
      spokenReply: "실제 발화",
      tools: "도구",
      silentReason: "무응답 이유",
      error: "오류",
      loadFailed: "실행 로그 로드 실패: {{message}}",
      noRecentLogs: "최근 로그가 없습니다.",
      noRecentLogsWithFile: "최근 로그가 없습니다 · {{path}}",
      recentCount: "최근 로그 {{count}}개{{fileSuffix}}.",
      unknownSource: "알 수 없음",
      runLabel: "실행",
      unknownState: "알 수 없음",
    },
    settings: {
      title: "설정",
      subtitle: "KIRA 엔진, Slack 어댑터, 모델 키를 한 곳에서 설정합니다.",
      language: "언어",
      theme: "테마",
      themeRed: "크래프톤 레드",
      themePubg: "PUBG 골드",
      identityTitle: "정체성",
      identityDesc: "이 데스크톱 에이전트가 앱과 Slack에서 보여줄 이름을 정합니다.",
      agentName: "에이전트 이름",
      persona: "페르소나",
      modelTitle: "모델",
      modelDesc: "엔진이 사용할 제공자와 필요한 키를 설정합니다.",
      provider: "제공자",
      modelOverride: "모델 오버라이드",
      personaPlaceholder: "차분하고 간결하며 실용적으로 행동합니다. 설명보다 행동을 우선하고, 그룹 공간에서는 정말 필요할 때만 말합니다.",
      anthropicApiKey: "Anthropic API 키",
      openaiApiKey: "OpenAI API 키",
      workspaceTitle: "워크스페이스",
      workspaceDesc: "브리지 모드는 단순하게 두고 `.kira`를 재사용하며, 이 에이전트가 사용할 워크스페이스를 선택하세요.",
      filesystemBaseDir: "파일시스템 기본 경로",
      statusReadFrom: "설정은 `~/.kira/config.env`에서 읽습니다.",
    },
    status: {
      savingSettings: "설정 저장 중...",
      restartingWithNewSettings: "새 설정으로 KIRA 엔진을 재시작하는 중...",
      engineRestartedWithNewSettings: "새 설정으로 KIRA 엔진을 재시작했습니다.",
      engineRestartFailed: "KIRA 엔진 재시작에 실패했습니다.",
      settingsSavedAndRestarted: "설정을 저장하고 엔진을 재시작했습니다.",
      settingsSavedButRestartFailed: "설정은 저장했지만 엔진 재시작은 실패했습니다.",
      settingsSavedToConfig: "설정을 ~/.kira/config.env에 저장했습니다.",
      saveFailed: "저장 실패: {{message}}",
      actionProgress: "KIRA 엔진 {{action}}...",
      actionCompleted: "KIRA 엔진 {{action}} 완료.",
      actionFailed: "KIRA 엔진 {{action}} 실패: {{message}}",
      openingChromeProfileSetup: "Chrome 프로필 설정을 여는 중...",
      chromeProfileSetupOpened: "Chrome 프로필 설정을 열었습니다.",
      profileSetupFailed: "프로필 설정 실패: {{message}}",
      filesystemBaseDirEmpty: "파일시스템 기본 경로가 비어 있습니다.",
      openingFilesystemBaseDir: "파일시스템 기본 경로를 여는 중...",
      filesystemBaseDirOpened: "파일시스템 기본 경로를 열었습니다.",
      skillFolderNotConfigured: "스킬 폴더가 설정되지 않았습니다.",
      openingSkillFolder: "스킬 폴더를 여는 중...",
      skillFolderOpened: "스킬 폴더를 열었습니다.",
      runLogFileNotConfigured: "로그 파일 경로가 설정되지 않았습니다.",
      openingRunLogFile: "로그 파일을 여는 중...",
      runLogFileOpened: "로그 파일을 열었습니다.",
      openFolderFailed: "폴더 열기 실패: {{message}}",
      skillLoadFailed: "스킬 로드 실패: {{message}}",
      slackRetrieveClientCredentialsRequired: "Slack Retrieve Client ID와 Client Secret이 필요합니다.",
      slackRetrieveStartEngineFirst: "Slack Retrieve를 연결하기 전에 KIRA 엔진을 먼저 시작하세요.",
      slackRetrieveOauthStarted: "Slack 인증을 시작했습니다.",
      slackRetrieveOauthRestarting: "Slack 연결이 완료되어 KIRA 엔진을 재시작하는 중입니다...",
      slackRetrieveOauthRestarted: "새 Slack Retrieve 토큰으로 KIRA 엔진을 재시작했습니다.",
      start: "시작 중",
      restart: "재시작 중",
      stop: "중지 중",
      updating: "업데이트 중",
    },
  },
};

let currentLanguage = "en";
let changeHandler = null;

function getNestedValue(object, key) {
  return key.split(".").reduce((value, part) => (value && value[part] !== undefined ? value[part] : null), object);
}

function detectDefaultLanguage() {
  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (saved === "ko" || saved === "en") {
    return saved;
  }
  const browserLanguage = String(window.navigator.language || "").toLowerCase();
  return browserLanguage.startsWith("ko") ? "ko" : "en";
}

function interpolate(template, options = {}) {
  let value = template;
  for (const [key, replacement] of Object.entries(options)) {
    value = value.replace(new RegExp(`{{${key}}}`, "g"), String(replacement));
  }
  return value;
}

function setTextContent(selector, value) {
  const element = typeof selector === "string" ? document.querySelector(selector) : selector;
  if (element) {
    element.textContent = value;
  }
}

export function getLanguage() {
  return currentLanguage;
}

export function getDateLocale() {
  return currentLanguage === "ko" ? "ko-KR" : "en-US";
}

export function t(key, options = {}) {
  let value = getNestedValue(translations[currentLanguage], key);
  if (value === null || value === undefined) {
    value = getNestedValue(translations.en, key);
  }
  if (typeof value !== "string") {
    return key;
  }
  return interpolate(value, options);
}

export function applyTranslations() {
  document.documentElement.lang = currentLanguage;

  for (const element of document.querySelectorAll("[data-i18n]")) {
    element.textContent = t(element.dataset.i18n);
  }

  for (const element of document.querySelectorAll("[data-i18n-placeholder]")) {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
  }

  for (const element of document.querySelectorAll("[data-i18n-title]")) {
    element.setAttribute("title", t(element.dataset.i18nTitle));
  }

  for (const element of document.querySelectorAll("[data-i18n-aria-label]")) {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  }

  setTextContent(".nav-item[data-view=\"overview\"] span:last-child", t("nav.home"));
  setTextContent(".nav-item[data-view=\"chat\"] span:last-child", t("nav.talk"));
  setTextContent(".nav-item[data-view=\"channel\"] span:last-child", t("nav.channels"));
  setTextContent(".nav-item[data-view=\"schedules\"] span:last-child", t("nav.schedules"));
  setTextContent(".nav-item[data-view=\"settings\"] span:last-child", t("nav.settings"));
  setTextContent(".nav-item[data-view=\"runs\"] span:last-child", t("nav.logs"));
  document.title = t("app.title");
}

export function setLanguage(language, { persist = true } = {}) {
  currentLanguage = language === "ko" ? "ko" : "en";
  if (persist) {
    window.localStorage.setItem(STORAGE_KEY, currentLanguage);
  }
  const selector = document.getElementById("ui-language");
  if (selector) {
    selector.value = currentLanguage;
  }
  applyTranslations();
  changeHandler?.(currentLanguage);
}

export function initI18n({ onChange } = {}) {
  changeHandler = onChange || null;
  currentLanguage = detectDefaultLanguage();
  const selector = document.getElementById("ui-language");
  if (selector) {
    selector.value = currentLanguage;
    selector.addEventListener("change", () => {
      setLanguage(selector.value);
    });
  }
  applyTranslations();
  return currentLanguage;
}
