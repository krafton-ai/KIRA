# 이미지 폴더 구조

이 폴더에 문서에 사용할 이미지를 저장하세요.

## 폴더 구조

```
public/images/
├── screenshots/        # 앱 스크린샷
│   ├── slack-setup.png
│   ├── kira-main.png
│   └── settings.png
├── icons/             # 아이콘
└── logos/             # 로고
```

## 사용 방법

### 마크다운에서 이미지 사용

```markdown
![설명](/images/screenshots/slack-setup.png)
```

### HTML 태그로 이미지 사용 (크기 조절)

```html
<img src="/images/screenshots/slack-setup.png" alt="Slack 설정" style="max-width: 600px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
```

### 이미지 캡션과 함께

```markdown
![Slack 설정 화면](/images/screenshots/slack-setup.png)
*Slack App 설정 화면*
```

## 추천 사항

- **형식**: PNG 또는 JPG
- **크기**: 최대 800-1000px 너비 (Retina 디스플레이 고려 시 @2x)
- **용량**: 가능한 최적화 (TinyPNG 등 사용)
- **파일명**: kebab-case 사용 (예: `slack-token-setup.png`)
