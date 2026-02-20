# Perplexity 웹 검색

Perplexity API를 연동하면 KIRA가 실시간 웹 정보를 검색할 수 있습니다.

## 📋 준비물

- Perplexity API 계정
- API 키

---

## 🔑 1단계: API 키 발급

### 1. Perplexity 계정 생성
1. [Perplexity AI](https://www.perplexity.ai/) 접속
2. 계정 생성 및 로그인

### 2. API 키 발급
1. [Perplexity API 페이지](https://www.perplexity.ai/settings/api) 접속
2. **"Generate API Key"** 클릭
3. API 키 복사 (나중에 사용)

::: tip API 사용료
Perplexity API는 사용량에 따라 과금됩니다.
무료 티어와 유료 플랜을 확인하세요.
:::

---

## ⚙️ 2단계: KIRA 설정

### 1. KIRA 앱 실행
환경변수 설정 탭을 엽니다.

### 2. Perplexity 섹션 찾기
**MCP 설정** > **Perplexity**

### 3. 설정 활성화
- 토글 스위치를 **켜기**로 변경

### 4. API 키 입력
- **PERPLEXITY_API_KEY**: 앞서 복사한 API 키

### 5. 설정 저장
- **"설정 저장"** 버튼 클릭
- 서버 재시작

---

## ✅ 3단계: 테스트

Slack에서 KIRA에게 물어보세요:

```
오늘 서울 날씨 어때?
```

```
최근 AI 뉴스 검색해줘
```

KIRA가 실시간 정보를 검색하여 답변합니다.

---

## 🎯 사용 예시

### 날씨 정보
```
사용자: 내일 부산 날씨 알려줘
KIRA: [Perplexity 검색] 내일 부산은 맑고 최고 기온 18도입니다...
```

### 최신 뉴스
```
사용자: 오늘 주요 뉴스 정리해줘
KIRA: [Perplexity 검색] 1. ... 2. ... 3. ...
```

### 실시간 정보
```
사용자: 비트코인 현재 가격은?
KIRA: [Perplexity 검색] 현재 비트코인 가격은...
```

---

## 🔧 문제해결

### "API key is invalid"
- API 키가 올바르게 입력되었는지 확인
- Perplexity 웹사이트에서 API 키가 활성화되었는지 확인

### "Rate limit exceeded"
- API 사용 한도를 초과했습니다
- Perplexity 대시보드에서 사용량 확인
- 유료 플랜으로 업그레이드 고려

### 검색 결과가 나오지 않음
- PERPLEXITY_ENABLED가 True로 설정되었는지 확인
- 서버를 재시작했는지 확인
- 로그에서 에러 메시지 확인

---

## 💡 팁

### 효과적인 검색 질문
- ✅ "2024년 11월 서울 날씨"
- ✅ "최근 1주일 AI 뉴스"
- ❌ "날씨" (너무 모호함)

### 비용 절감
- 필요할 때만 웹 검색 요청
- 간단한 질문은 KIRA의 기본 지식으로 답변 가능
