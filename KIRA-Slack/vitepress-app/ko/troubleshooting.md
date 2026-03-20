# 문제 해결

## macOS에서 앱을 열 수 없다고 나와요

현재 빌드가 아직 공증되지 않았으면 첫 실행에서 macOS 경고가 뜰 수 있습니다.

이렇게 열면 됩니다.

1. Finder에서 `KiraClaw.app` 찾기
2. 앱을 우클릭
3. `열기` 선택
4. 한 번 더 확인

한 번 열고 나면 이후 실행은 보통 정상입니다.

## 아직 예전 KIRA-Slack 앱이 열려요

이 경우 아직 legacy 앱을 실행하고 있는 겁니다.

다음 앱을 열었는지 확인하세요.

- `KiraClaw.app`

예전 `KIRA` 앱이 아니라 새 `KiraClaw` 앱을 실행해야 합니다.

## KIRA-Slack이 제자리 자동 업데이트될 줄 알았어요

`KIRA-Slack`은 이제 legacy로 취급됩니다.

수동 전환 기준으로 보면 됩니다.

1. 최신 `KiraClaw` 다운로드
2. 새 앱으로 설치
3. 필요하면 기존 `~/.kira` 설정 재사용

## 현재 KiraClaw에서는 업데이트가 어떻게 보이나요?

KiraClaw는 업데이트를 다음 시점에 확인합니다.

- 앱 시작 시 한 번
- `Home` 화면에 들어갈 때 한 번

`Home`에 버튼이 항상 보이는 것은 아닙니다.

- 이미 최신이면 버튼이 보이지 않습니다
- 새 버전이 있으면 `Update to vX`가 나타납니다
- 다운로드가 끝나면 `Restart to Update`로 바뀝니다

앱을 오래 켜둔 상태라면 `Home`으로 다시 들어가서 업데이트 상태를 새로 확인하세요.

## Slack이나 Telegram이 응답하지 않아요

데스크톱 앱에서 다음을 확인하세요.

- `Channels`
- `Logs`

runtime은 정상인데 바깥으로 말하지 않았다면, `Logs` 화면에서 다음을 보면 됩니다.

- internal summary
- spoken reply
- tool usage
- silent reason

## OpenAI에서 tools 배열 에러가 나요

OpenAI provider 사용 중 아래와 같은 에러가 보이면:

- `Invalid 'tools': array too long`
- `Expected an array with maximum length 128`

현재 요청에 붙은 tool 수가 너무 많다는 뜻입니다.

보통 여러 MCP 서버를 동시에 켰을 때 발생합니다.

이렇게 해결하면 됩니다.

1. `Settings > MCP` 열기
2. 지금 당장 필요 없는 MCP 서버 몇 개 끄기
3. 엔진 재시작
4. 다시 실행

tool을 많이 켠 상태를 유지하고 싶다면, 현재 OpenAI chat 경로보다 더 많은 tool을 잘 버티는 provider/model 조합을 사용하는 것도 방법입니다.

## 로컬 파일은 어디에 있나요?

KiraClaw는 filesystem base directory 아래에 상태를 둡니다.

- `skills/`
- `memories/`
- `schedule_data/`
- `logs/`

관련 폴더는 데스크톱 앱에서 바로 열 수 있습니다.
