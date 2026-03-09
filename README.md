<table align="center"><tr><td>

```
                          ●      ●

                        ▄████◣◢████▄
                     ◥▄████▀▀  ▀▀████▄◤
                        ▀▀        ▀▀

 _____ ___ ___ __  __ ___ _  _ _   _ ___     _  _____ ___    _
|_   _| __| _ \  \/  |_ _| \| | | | / __|___| |/ /_ _| _ \  /_\
  | | | _||   / |\/| || || .` | |_| \__ \___| ' < | ||   / / _ \
  |_| |___|_|_\_|  |_|___|_|\_|\___/|___/   |_|\_\___|_|_\/_/ \_\
```

</td></tr></table>

<p align="center">
  A smarter agent harness for <a href="https://github.com/laude-institute/terminal-bench">Terminal-Bench</a>, built on <a href="https://github.com/laude-institute/terminal-bench">Terminus 2</a>
  <br/>
  <em>Simple fixes, significant gains.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Codex_5.3-75.5%25-blue?style=for-the-badge" alt="Codex 5.3: 75.5%">
  <img src="https://img.shields.io/badge/Opus_4.6-75.7%25-blueviolet?style=for-the-badge" alt="Opus 4.6: 75.7%">
  <img src="https://img.shields.io/badge/Gemini_3.1_Pro-74.8%25-orange?style=for-the-badge" alt="Gemini 3.1 Pro: 74.8%">
</p>

## What is Terminus-KIRA?

Terminus-KIRA is an agent harness for [Terminal-Bench](https://github.com/laude-institute/terminal-bench), built on top of [Terminus 2](https://github.com/laude-institute/terminal-bench). It boosts frontier model performance on Terminal-Bench through a set of minimal but effective harness-level improvements — native tool calling, multimodal support, execution optimization, and smarter completion verification.

---

## Key Features

- **Native Tool Calling** — Replaces ICL JSON/XML parsing with the LLM `tools` parameter for structured, reliable outputs
- **Image Analysis (Multimodal)** — `image_read` tool for base64-encoded image analysis directly from the terminal
- **Marker-based Polling** — Early command completion detection using echo markers, cutting unnecessary wait time
- **Smart Completion Verification** — Double-confirmation checklist covering requirements, robustness, and multi-perspective QA (test engineer, QA engineer, user)
- **Prompt Caching** — Anthropic ephemeral caching on recent messages to reduce latency and cost

---

## Architecture

Terminus-KIRA extends Terminus 2 by replacing its ICL (In-Context Learning) response parsing with native LLM tool calling.

**Tool definitions** passed via the `tools` parameter:

| Tool | Purpose |
|---|---|
| `execute_commands` | Run shell commands with analysis and plan |
| `task_complete` | Signal task completion (triggers double-confirmation) |
| `image_read` | Analyze image files via base64 multimodal input |

**How it works:**

1. Calls `litellm.acompletion` directly with `tools=TOOLS`, bypassing the base `Chat` class to access native tool calling
2. The model returns structured tool calls instead of free-form text — no regex/JSON parsing needed
3. On context window overflow, automatically summarizes conversation history and retries
4. Marker-based polling appends `echo '__CMDEND__<seq>__'` after each command; if the marker appears before the requested duration, execution moves on immediately

---

## Evolution

Key milestones from development history:

| # | Milestone | Description |
|---|---|---|
| 1 | Genesis | Copy of Terminus 2 as starting point |
| 2 | Native Tool Use | Replaced ICL JSON/XML parsing with LLM `tools` parameter |
| 3 | Output Limiting | 30 KB cap on terminal output to prevent context bloat |
| 4 | Autonomy & Constraints | Prompt engineering for agent autonomy and environment constraints |
| 5 | Completion Confirmation | Include original instruction in completion check |
| 6 | Multimodal | `image_read` tool for visual analysis of terminal screenshots |
| 7 | Completion Checklist | Multi-perspective QA checklist (test engineer, QA, user) |
| 8 | Execution Optimization | Marker-based polling and block timeout protection |
| 9 | Temperature Fix | Set temperature to 1 when using reasoning effort |

---

## Usage

```bash
uv run harbor run \
    --dataset terminal-bench-sample@2.0 \
    --n-tasks 1 \
    --agent-import-path "terminus_kira.terminus_kira:TerminusKira" \
    --model anthropic/claude-opus-4-6 \
    --env docker \
    -n 1
```

For more details, visit our [blog post](https://krafton-ai.github.io/blog/terminus_kira_en/).

---

## Project Structure

```
├── terminus_kira/
│   ├── __init__.py
│   └── terminus_kira.py        # Main agent (native tool calling)
├── prompt-templates/
│   └── terminus-kira.txt        # System prompt
├── run-scripts/
│   ├── run_docker.sh            # Local Docker execution
│   ├── run_daytona.sh           # Daytona cloud execution
│   └── run_runloop.sh           # Runloop cloud execution
├── anthropic_caching.py         # Prompt caching utility
└── pyproject.toml
```

---

## Citing Us

If you found Terminus-KIRA useful, please cite us as:

```bibtex
@misc{terminuskira2026,
      title={Terminus-KIRA: Boosting Frontier Model Performance on Terminal-Bench with Minimal Harness },
      author={{KRAFTON AI} and {Ludo Robotics}},
      year={2026},
      url={https://github.com/krafton-ai/kira},
}
```

---

## Changelog

| Version | Description |
|---|---|
| **v1.1** | Migrated from In-Context Learning (ICL) to **native tool calling** via LLM `tools` parameter. Removed verbose JSON/XML response format instructions from system prompt — the model now receives structured tool definitions directly, resulting in a significantly shorter prompt and more reliable outputs. |
| **v1.0** | Initial release. Fork of Terminus 2 with ICL-based JSON response parsing and full response format instructions in the system prompt. |

---
KRAFTON AI & Ludo Robotics
