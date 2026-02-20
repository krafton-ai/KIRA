# Scoring Examples

실제 상황별 점수 계산 예시입니다.

## Pattern 1: 조사 (threshold: 5)

**Example: 기술 선택 (7점, 제안)**
```
메시지: "결제 게이트웨이 뭐 쓸까? Stripe vs Toss Payments"
채널: #개발팀
멘션: @팀장 @개발1 @개발2

Base: 2 (키워드 명확)
옵션: +1 (vs)
시급성: +2 (high priority)
영향도: +2 (3명)
= 7점 ≥ 5점 → ✅ 제안
```

## Pattern 2: 스케줄링 (threshold: 5)

**Example: 팀 회의 (8점, 제안)**
```
메시지: "@all 이번주 Q4 리뷰 회의"
채널: #경영팀 (7명)

Base: 2
참석자: +1 (@all)
인원: +4 (7명)
시급성: +2 (이번주)
= 9점 ≥ 5점 → ✅ 제안
```

## Threshold 조정 가이드

```
수용률 < 30%: threshold +1~2점
수용률 30-50%: threshold +0.5점
수용률 50-70%: 유지
수용률 > 70%: threshold -0.5~1점
```

