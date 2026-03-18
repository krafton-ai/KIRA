# 시작하기

이 가이드는 일부러 짧게 유지합니다. 예전 `KIRA-Slack` 설정 표면은 이제 메인 제품 경로가 아닙니다.

새 설치는 `KiraClaw` 기준으로 진행하세요.

## 1. 다운로드

- macOS (Apple Silicon): [KiraClaw for macOS 다운로드](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-arm64.dmg)
- Windows: [KiraClaw for Windows 다운로드](https://kira.krafton-ai.com/download/kiraclaw/KiraClaw-0.1.60-x64.exe)

## 2. 설치

### macOS

1. `.dmg`를 엽니다
2. `KiraClaw.app`를 `Applications`로 복사합니다
3. 앱을 실행합니다

첫 실행에서 macOS 경고가 뜨면 [문제 해결](/ko/troubleshooting)을 참고하세요.

### Windows

1. 설치 파일을 실행합니다
2. 설치 마법사를 끝냅니다
3. `KiraClaw`를 실행합니다

## 3. 워크스페이스 선택

KiraClaw는 다음을 위한 로컬 filesystem base directory를 사용합니다.

- `skills/`
- `memories/`
- `schedule_data/`
- `logs/`

현재 기본 workspace는 보통 `~/Documents/KiraClaw` 아래를 사용합니다.

## 4. 데스크톱 앱 열기

앱에서 먼저 보면 되는 화면은 다음입니다.

- `Talk`
- `Channels`
- `Skills`
- `Schedules`
- `Logs`

## 5. 선택: 채널 연결

현재 채널은 다음을 지원합니다.

- Slack
- Telegram
- Discord

채널 설정은 데스크톱 `Channels` 화면에서 합니다.

## 6. Identity와 persona

`Settings > Identity`에서 다음을 설정합니다.

- agent 이름
- persona 줄글

## 7. 런타임 확인

가장 쉬운 smoke test는:

1. `Talk` 열기
2. 짧은 질문하기
3. internal summary와 spoken reply가 둘 다 보이는지 확인하기

## KIRA-Slack에서 전환

`KIRA-Slack`은 이제 legacy로 취급됩니다.

기존 `KIRA-Slack`를 썼다면 KiraClaw는 여전히 다음을 재사용할 수 있습니다.

- `~/.kira/config.env`
- `~/.kira/credential.json`

즉 모든 설정을 처음부터 다시 만들지 않고도 앞으로 이동할 수 있습니다.
