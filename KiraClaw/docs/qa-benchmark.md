# KiraClaw QA Benchmark

This checklist is for manual QA of the current KiraClaw product shell.
It focuses on observable behavior, not implementation details.

## Test setup

- Use the latest KiraClaw desktop build or dev app.
- Confirm the engine is running before chat tests.
- Use the current workspace at `Filesystem Base Dir`.
- If Slack or Telegram are part of the pass, use an allowed user name.

## Pass criteria

- Every requested action either completes correctly or fails with a clear user-facing error.
- No silent hangs longer than expected startup/tool latency.
- Generated files are accessible from the desktop app or attached back to the channel when supported.
- Multi-turn context works within the same session/thread/chat.

## 1. Desktop shell

### 1.1 Startup

Prompt or action:
- Open the desktop app.
- Start the engine.

Expected:
- Home shows the engine as online.
- No false offline state after tab switches.
- App remains resizable and usable.

Failure signs:
- Home stays offline while `/health` is healthy.
- App starts but controls are frozen.

### 1.2 Navigation

Action:
- Visit `Talk`, `Channels`, `MCP`, `Skills`, `Schedules`, `Watches`, `Settings`.

Expected:
- Each tab renders without layout breakage.
- Titles match sidebar labels.
- No input fields reset while typing.

## 2. Talk

### 2.1 Basic response

Prompt:
- `지금 몇시야? 정확히 확인해서 알려줘`

Expected:
- A normal reply returns.
- Tool trace appears when tools are used.

### 2.2 Multi-turn

Prompt sequence:
1. `비밀 단어는 lobster야. ok만 답해`
2. `내가 방금 기억하라고 한 단어만 말해`

Expected:
- Second answer returns `lobster`.

### 2.3 File creation and path handling

Prompt:
- `workspace files 폴더에 test-note.txt를 만들고 경로를 알려줘`

Expected:
- Reply includes an absolute path.
- The path is clickable in `Talk`.
- Clicking it reveals the file in Finder.

Failure signs:
- Path is plain text only.
- Clicking does nothing or opens the wrong folder.

## 3. Slack

### 3.1 DM response

Prompt:
- Send a DM from an allowed user.

Expected:
- Bot replies in the same DM.

### 3.2 Multi-turn in DM or thread

Prompt sequence:
1. `내 프로젝트 이름은 Project Coral이야`
2. `내 프로젝트 이름이 뭐였지?`

Expected:
- Follow-up answer uses previous context.

### 3.3 File return

Prompt:
- `나스닥 어제 주요 지표 찾아서 pdf로 만들어서 보내줘`

Expected:
- Summary text is sent.
- A PDF is uploaded to Slack.

Failure signs:
- Bot says a file exists but only gives a local path.
- No file is attached.

### 3.4 Unauthorized user

Action:
- Message the bot from a user name outside `Allowed Names`.

Expected:
- No reply.
- No visible side effects.

## 4. Telegram

### 4.1 DM response

Prompt:
- Send a DM from an allowed Telegram account.

Expected:
- Bot replies in the same chat.

### 4.2 File return

Prompt:
- `간단한 pdf를 만들어서 여기로 보내줘`

Expected:
- Bot sends the file back into the same Telegram chat.

Failure signs:
- Bot only says the file was created locally.
- No Telegram file appears.

### 4.3 Unauthorized user

Action:
- Message from an account outside `Allowed Names`.

Expected:
- No reply.

## 5. Skills

### 5.1 Discovery

Action:
- Open the `Skills` tab.

Expected:
- Registered skills appear from `Filesystem Base Dir/skills`.

### 5.2 Skill creation

Prompt:
- `slack icon gif 만드는 skill 만들어줘`

Expected:
- A new skill folder is created under `Filesystem Base Dir/skills`.
- The new skill appears in the `Skills` tab after refresh or next run.

## 6. Memory

### 6.1 Save and retrieve

Prompt sequence:
1. `우리 팀 색상 규칙은 navy와 white야`
2. Start a new local session.
3. `우리 팀 색상 규칙이 뭐였지?`

Expected:
- The new session can recall the rule from long-term memory.

## 7. Schedules

### 7.1 Visibility

Action:
- Open the `Schedules` tab.

Expected:
- Existing schedules from `schedule_data/schedules.json` are listed.

### 7.2 Integrity

Expected:
- UI matches the underlying schedule count.
- Broken or empty state is surfaced clearly.

## 8. Watches

### 8.1 Create and run

Action:
- Create a watch with:
  - Every N Minutes: `30`
  - Condition: `현재 시간을 확인한다`
  - Action: `아무것도 하지 말고 짧게 요약한다`
- Save.
- Run now.

Expected:
- Watch saves successfully.
- Run history records the execution.

### 8.2 Isolation

Expected:
- Watch runs do not pollute chat memory.

## 9. MCP

### 9.1 Time MCP

Prompt:
- `서울이랑 샌프란시스코 현재 시간 비교해줘`

Expected:
- A correct answer returns.
- Runtime stays healthy.

### 9.2 Browser MCP

Prompt:
- `브라우저 mcp를 사용해서 네이버에서 크래프톤 주가 찾아줘`

Expected:
- If browser setup is ready, the run completes.
- If not ready, failure is explicit rather than hanging forever.

## 10. Known weak points to watch

- Engine startup latency can be high when many MCP servers are enabled.
- Custom remote MCP failures should not break the rest of the runtime.
- File-return behavior should be checked separately for Slack and Telegram.
- Desktop still lacks full automated e2e coverage.

## Suggested QA outcome labels

- `PASS`: behavior matches expected output.
- `PASS WITH NOTE`: works but latency or UX needs polish.
- `FAIL`: behavior is broken or missing.
- `BLOCKED`: cannot verify because external credentials or environment are missing.
