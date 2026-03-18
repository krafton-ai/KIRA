# 🤖 KIRA - AI Virtual Coworker

> [!IMPORTANT]
> **KIRA-Slack is now legacy software.** It will not receive new feature updates.
> Please install **KiraClaw** for all new usage and future updates: [https://kira.krafton-ai.com](https://kira.krafton-ai.com)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18.0.0-green)](https://nodejs.org/)
[![Electron](https://img.shields.io/badge/electron-latest-9feaf9)](https://www.electronjs.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey)]()
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

**24/7 AI agent powered by Claude, running entirely on your desktop**

*No server setup. No cloud required. Just install the app and start working.*

---

## 📖 Documentation

**👉 [User Guide](https://kira.krafton-ai.com) - Complete setup and usage guide**

---

## 💡 What is KIRA?

> **KIRA** = **K**RAFTON **I**NTELLIGENCE **R**OOKIE **A**GENT

KIRA is an open-source project that repackages **KRIS (KRAFTON Intelligence System)**—an AI agent system successfully used internally at KRAFTON—into a "virtual coworker" concept that anyone can install and use as a standalone desktop application.

### 🎬 Demo

| Search + PPTX | GitRepo + PDF | Web + Wiki |
|:---:|:---:|:---:|
| <video src="https://github.com/user-attachments/assets/284f9d0d-056c-42e9-8f1f-19873431ddba" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/721bc704-8b1a-4673-829a-52309ae69601" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/7329039a-fdad-4f4b-8f03-65402e4d6f6c" width="240" controls></video> |

| Proactive + Thread | Email + Schedule | Proactive + Translate |
|:---:|:---:|:---:|
| <video src="https://github.com/user-attachments/assets/9ee1a520-507c-408a-a1d2-4a7a393385eb" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/79959017-67c2-4109-98bd-8c1dbba2b34f" width="240" controls></video> | <video src="https://github.com/user-attachments/assets/c78768be-580e-42e8-a3d8-34eb5f0db6cb" width="240" controls></video> |

KIRA is an **AI virtual coworker** that runs as a desktop application. Once installed:

- 🤖 **Chat in Slack**: Natural conversations in DMs, channels, and threads
- 📧 **Email Monitoring**: Auto-extract tasks from Outlook emails
- 📝 **Document Tracking**: Monitor Confluence and Jira updates
- 🧠 **Memory System**: Automatically remembers conversations and project context
- 🔒 **Privacy First**: All data and memory stored locally — no third-party services involved
    - Your conversation history, memory files, and settings are stored only on your machine
    - KIRA communicates directly with Anthropic's Claude API using your own API key
    - Unlike third-party AI services, no intermediary stores or accesses your data
    - We do not collect, store, or process any user data — see [Data Privacy Disclaimer](#%EF%B8%8F-data-privacy--liability-disclaimer)
- 🔑 **Bring Your Own API Key**: Transparent, pay-as-you-go costs with your own Claude API key — no subscriptions or hidden fees

### Two Usage Modes

**🤖 Bot Mode**
- Install on **your computer**
- Use your own Slack account or bot app
- Personal AI assistant that you manage
- Stops when your computer is off

**👤 Virtual Coworker Mode**
- Install on a **dedicated computer** (or VM/server)
- Create a dedicated Slack account for the AI (e.g., "KIRA Kim")
- Runs 24/7 independently as a real team member
- Shared by the entire team

> 💡 **KRAFTON Use Case**: KRAFTON provides a dedicated company account and computer to run KIRA as a virtual coworker, just like onboarding a new hire.

---

## 🚀 Quick Start

### 1. Prerequisites

- macOS 10.15 or later / Windows 11 or later
- Slack workspace (admin access required)
- Claude API key (Google Cloud Vertex AI)

### 2. Download and Install

**Download the latest release:**
```
https://kira.krafton-ai.com
```

Or build from source:

```bash
# Clone repository
git clone https://github.com/krafton-ai/kira.git
cd kira

# Install Python dependencies
uv sync

# Build Electron app
cd electron-app
npm install
npm run build

# Install the generated .dmg file
open dist/KIRA-*.dmg
```

### 3. Create Slack App

Follow the detailed guide: **[Slack App Setup](https://kira.krafton-ai.com/setup/slack-app)**

### 4. Configure KIRA

1. Launch KIRA app
2. Enter Slack tokens in Settings
3. Configure bot information
4. Click "Save Settings" and "Start"

### 5. Test in Slack

```
@KIRA Hello!
```

🎉 **Done!** You can now chat with KIRA.

---

## 📁 Project Structure

```
kira/
├── app/                   # Python AI server
│   ├── main.py           # Server entry point
│   ├── cc_agents/        # AI agent modules
│   ├── cc_checkers/      # Proactive monitors (email, docs)
│   ├── cc_tools/         # MCP tool implementations
│   ├── cc_web_interface/ # Web interface (voice input)
│   └── config/           # Configuration files
│
├── electron-app/         # Electron desktop app
│   ├── main.js          # Electron main process
│   ├── renderer/        # UI (settings, logs)
│   └── dist/            # Build output (.dmg)
│
├── vitepress-app/       # Documentation site
│   ├── index.md         # Homepage
│   ├── getting-started.md
│   ├── setup/           # Setup guides
│   └── features/        # Features guide
│
└── README.md            # This file
```

---

## 🧠 Agent Architecture

KIRA uses a multi-agent pipeline where each agent has a specific role. This design enables cost optimization (simple tasks use lighter models) and clear separation of concerns.

### Message Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  SLACK MESSAGE RECEIVED                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  DEBOUNCING (2 sec)                                         │
│  - Merge consecutive messages from same user                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  BOT CALL DETECTOR (Haiku)                                  │
│  - Determine if message requires bot response               │
│  - DM: Always respond                                       │
│  - Channel: Only when mentioned                             │
│  - Thread: Additional context analysis                      │
└─────────────────────────────────────────────────────────────┘
                 ↓                              ↓
    ┌────────────────────┐         ┌────────────────────────┐
    │  SIMPLE CHAT       │         │  OPERATOR              │
    │  (Haiku, no MCP)   │         │  (Opus, full MCP)      │
    │  - Quick responses │         │  - Complex tasks       │
    │  - Casual chat     │         │  - Tool execution      │
    └────────────────────┘         └────────────────────────┘
              ↓                              ↓
              └──────────────┬───────────────┘
                             ↓
              ┌────────────────────────────────┐
              │  MEMORY MANAGER (Sonnet)       │
              │  - Save conversation context   │
              │  - Organize into categories    │
              └────────────────────────────────┘
```

### Agent Inventory

| Agent | Model | MCP | Purpose |
|-------|-------|-----|---------|
| **Bot Call Detector** | Haiku | ❌ | Determine if bot should respond |
| **Thread Context Detector** | Haiku | ❌ | Analyze thread context for relevance |
| **Simple Chat** | Haiku | ❌ | Handle casual conversations quickly |
| **Memory Retriever** | Haiku | ✅ | Search relevant memories before responding |
| **Operator** | Opus | ✅ | Execute complex tasks with MCP tools |
| **Memory Manager** | Sonnet | ✅ | Save and organize conversation memories |
| **Answer Aggregator** | Sonnet | ✅ | Collect and process pending answers |
| **Proactive Suggester** | Sonnet | ✅ | Generate proactive task suggestions |
| **Proactive Confirm** | Haiku | ✅ | Request user approval for suggestions |

### 3-Tier Queue System

KIRA uses a hierarchical queue system to handle concurrent messages efficiently:

```
┌─────────────────────────────────────────────────────────────┐
│  CHANNEL QUEUES (per-channel)                               │
│  - 8 workers per channel                                    │
│  - Fast response for simple messages                        │
│  - Independent processing per channel                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR QUEUE (global)                                │
│  - 3 workers                                                │
│  - Heavy tasks requiring MCP tools                          │
│  - Prevents API rate limiting                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  MEMORY QUEUE (global)                                      │
│  - 1 worker (sequential)                                    │
│  - Ensures consistent file system writes                    │
│  - Prevents race conditions in memory storage               │
└─────────────────────────────────────────────────────────────┘
```

**Why this design?**
- **Channel Queues**: Users in different channels get fast responses without blocking each other
- **Orchestrator Queue**: Limits concurrent heavy tasks to prevent excessive CPU/memory usage
- **Memory Queue**: Single worker ensures no conflicts when writing to local memory files

---

## 🎯 Key Features

### Core Features
- **Chat**: Natural conversations in Slack DMs, channels, and threads
- **Task Execution**: Search, document writing, email management, Jira/GitLab integration
- **Memory System**: Auto-remembers team info and project context
- **Task Scheduling**: Execute tasks at specific times

### Proactive Monitors (Beta)
- **Email Monitoring**: Auto-check Outlook emails (5min interval)
- **Confluence Tracking**: Document update notifications (1hr interval)
- **Jira Tracking**: Monitor assigned issues (30min interval)

### Proactive Suggestions (Beta)
- Analyzes memory and proactively suggests needed tasks
- 7 intervention patterns (research, scheduling, documentation, drafting, connecting, predicting, routine)

### MCP Integrations
- Perplexity (web search)
- DeepL (translation)
- Outlook (email)
- Confluence & Jira (Rovo MCP)
- GitLab (code repository)
- X (Twitter)
- Clova Speech (transcription, meeting notes)
- Playwright (browser automation)

---

## 🛠️ Development

### Running Development Server

```bash
# Python server (hot reload)
uv run python dev.py

# Electron app (separate terminal)
cd electron-app
npm start
```

### Building

```bash
# Build macOS installer
cd electron-app
npm run build

# Output: electron-app/dist/KIRA-*.dmg
```

### Documentation Site

```bash
# Run docs dev server
cd vitepress-app
npm install
npm run docs:dev

# Deploy to S3
npm run deploy
```

---

## 💾 Data Storage

### App Settings
```
~/.kira/
├── config.env          # Environment variables
└── server.log          # Server logs
```

### Data and Memory
```
~/Documents/KIRA/       # FILESYSTEM_BASE_DIR
├── db/                 # SQLite databases
│   ├── waiting_answer.db
│   ├── confirm.db
│   ├── email_tasks.db
│   └── jira_tasks.db
└── memories/           # Memory (Markdown files)
    ├── channels/
    ├── projects/
    ├── users/
    ├── decisions/
    └── index.md
```

---

## 🔐 Security

- ✅ All memory, logs, and settings stored locally on your machine
- ✅ Direct communication with Claude API — no intermediary services
- ✅ External connections only to Claude API and MCP servers you enable

---

## 📖 Detailed Documentation

For complete setup and usage guides, visit **[KIRA Documentation](https://kira.krafton-ai.com)**

- [Getting Started](https://kira.krafton-ai.com/getting-started)
- [Setup Guides](https://kira.krafton-ai.com/setup/)
- [Features Guide](https://kira.krafton-ai.com/features/)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## ⚠️ Data Privacy & Liability Disclaimer

KIRA is a privacy-first AI agent. All memory, logs, and settings are stored on your device. Prompts are sent to Anthropic's Claude API using your own API key — no intermediary services are involved.

### How Your Data Flows

| Data Type | Where It Goes |
|-----------|---------------|
| Conversation memory, settings, logs | Your machine only |
| Prompts and queries | Anthropic Claude API (via your API key) |
| Usage history, analytics | Nowhere — we don't collect anything |

**Unlike third-party AI tools built on LLM providers, KIRA doesn't add another layer that stores your data. Your information goes to one place (Anthropic), not two.**

### 1. No Data Collection

KRAFTON does NOT collect, store, or process any user data. All data and memory are stored locally on your computer and under your sole control.

### 2. User Responsibility

You are responsible for managing your own Claude API key and usage, including any usage fees and security.

### 3. Third-Party Integration

KRAFTON is not responsible or liable for any data processed through, or any actions taken by, third-party services (e.g., Slack, Outlook, Confluence, Jira, GitLab, Anthropic Claude API) that you choose to integrate with KIRA. By using KIRA, you agree to comply with all applicable third-party terms, including Anthropic's Claude API Terms of Service.

### 4. No Warranty

This software is provided "AS IS", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement. In no event shall KRAFTON or any contributor be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

---

## ™️ Trademark Policy

The names **KRAFTON**, **KIRA**, and associated logos are trademarks of KRAFTON, Inc.
Permission to use these trademarks is not granted by the open-source license and requires separate written permission.

---

## 📚 Third-Party Libraries

KIRA incorporates open-source libraries under MIT, Apache-2.0, BSD, ISC, MPL-2.0, and other compatible licenses.
For a complete list of dependencies and their licenses, please refer to the [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) file.

---

## 🙏 Acknowledgments

- Built with [Claude](https://www.anthropic.com/claude) by Anthropic
- Powered by [Electron](https://www.electronjs.org/)
- Documentation by [VitePress](https://vitepress.dev/)

---

**Made with ❤️ by [KRAFTON AI](https://www.krafton.ai)**


## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=krafton-ai/KIRA&type=date&legend=top-left)](https://www.star-history.com/#krafton-ai/KIRA&type=date&legend=top-left)
