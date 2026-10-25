# AntiRoute ✦

<p align="center">
  <pre align="center">
    ___          __  _  ____             __       
   /   |  ____  / /_(_)/ __ \____  __  __/ /____  
  / /| | / __ \/ __/ // /_/ / __ \/ / / / __/ _ \ 
 / ___ |/ / / / /_/ // _, _/ /_/ / /_/ / /_/  __/ 
/_/  |_/_/ /_/\__/_//_/ |_|\____/\__,_/\__/\___/  
  </pre>
  <p align="center">
    <strong>The Antigravity AI Agent Router & TUI</strong><br />
    <em>Run Claude Code, Hermes, OpenCode, and Aider on Google Antigravity Gemini with zero API costs.</em>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/Python-3.10+-brightgreen.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Protocols-Anthropic%20%7C%20OpenAI-purple.svg" alt="Protocols">
  <img src="https://img.shields.io/badge/Backend-Google%20Antigravity%20Gemini-orange.svg" alt="Backend">
</p>

---

## What is AntiRoute?

**AntiRoute** is an open-source gateway, protocol router, and interactive terminal user interface (TUI) that bridges **Google Antigravity's Gemini models** (Gemini 3.8 Flash, 3.1 Pro, etc.) with leading autonomous coding agents and developer CLIs.

By translating between **Anthropic Messages API** (`/v1/messages`), **OpenAI API** (`/v1/chat/completions`), and native **Gemini schemas**, AntiRoute lets you run:
* **Claude Code** (Anthropic CLI)
* **Hermes Agent** (Nous Research)
* **OpenCode** (AI SDK coding agent)
* **Aider** (Pair programming CLI)
* **Goose** (Block developer agent)
* **Cline & Roo Code** (VS Code extensions)
* **Continue.dev** & custom Python/LangChain agents

...all directly powered by your Google Antigravity OAuth quota without paying per-token API fees.

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│  Agents: Claude Code / Hermes / OpenCode / Aider / ...  │
└───────────────────────────┬────────────────────────────┘
                            │ Speaks Anthropic (/v1/messages)
                            │ or OpenAI (/v1/chat/completions)
                            ▼
┌────────────────────────────────────────────────────────┐
│                  AntiRoute (Port 8317)                 │
│         Translates schemas to Gemini protocols         │
└───────────────────────────┬────────────────────────────┘
                            │ Authenticates via Antigravity OAuth (.auth/)
                            ▼
┌────────────────────────────────────────────────────────┐
│                  Google Antigravity                    │
│           Gemini 3.8 Flash / 3.1 Pro Models            │
└────────────────────────────────────────────────────────┘
```

---

## Quickstart

### 1. Authenticate with Antigravity
Log in with your Google account to generate OAuth credentials in `.auth/`:
```bash
./login-antigravity.sh
# If on SSH or a headless server without a browser:
./login-antigravity.sh --no-browser
```

### 2. Install System Shortcuts
Install the `antiroute` CLI and agent launchers to `~/.local/bin`:
```bash
./install.sh
```

### 3. Launch the Interactive TUI
```bash
antiroute
# or locally: ./antiroute
```

---

## Interactive TUI Cockpit

Launch the cockpit anytime with `antiroute`:

* **`[1] Dashboard`**: Real-time daemon status, PID, port, latency, and active Google account.
* **`[2] Agent Connect Hub`**: One-click connection guides, launchers, and exportable `.env` files for Hermes, OpenCode, Claude Code, Aider, Goose, Cline, etc.
* **`[3] Service Controls`**: Start, stop, or restart the proxy daemon, authenticate OAuth, and run live test queries.
* **`[4] Models Directory`**: Browse all available models from `/v1/models`. Press `[T]` to test any model, or press `[D]` to set it as the default target model in `config.yaml`.
* **`[5] Live Logs`**: Real-time scrolling and inspection of `proxy.log`.
* **`[6] Help & Shortcuts`**: Instant keybinding cheat sheet.

---

## Agent Quick Connect

###  Hermes Agent
```bash
# Option A: One-click launcher
antiroute-hermes

# Option B: Sourcing environment
source ./export-env.sh hermes
hermes
```

###  OpenCode
OpenCode is automatically configured with the `antigravity` provider:
```bash
# Option A: One-click launcher
antiroute-opencode

# Option B: Direct invocation
opencode -m antigravity/gemini-3.8-flash-high
```

###  Claude Code
```bash
# Option A: One-click launcher
antiroute-claude

# Option B: Manual export
export ANTHROPIC_BASE_URL="http://127.0.0.1:8317"
export ANTHROPIC_API_KEY="sk-antigravity-claude"
claude
```

###  Aider
```bash
aider --openai-api-base "http://127.0.0.1:8317/v1" \
      --openai-api-key "sk-antigravity-claude" \
      --model openai/gemini-3.8-flash-high
```

###  Cline / Roo Code (VS Code Extension)
In extension settings, select **OpenAI Compatible**:
* **Base URL**: `http://127.0.0.1:8317/v1`
* **API Key**: `sk-antigravity-claude`
* **Model ID**: `gemini-3.8-flash-high`

---

## CLI Reference

`antiroute` can also be used as a non-interactive CLI in scripts:

| Command | Action |
|---|---|
| `antiroute` | Launch interactive TUI cockpit |
| `antiroute status` | Display service status, latency, and OAuth tokens |
| `antiroute test` | Run test queries on both Anthropic and OpenAI endpoints |
| `antiroute connect` | Display overview of all supported agents and export commands |
| `antiroute connect <tool>` | Print detailed configuration for a specific agent |
| `antiroute connect <tool> --export` | Export `.env.<tool>` file |
| `antiroute start` | Start the background proxy daemon |
| `antiroute stop` | Stop the running proxy daemon |
| `antiroute restart` | Restart the proxy daemon |

---

## Background Service (systemd)

To run AntiRoute continuously in the background and auto-start on boot/login:

```bash
# Install systemd user service
./setup-systemd.sh install

# Enable on boot
systemctl --user enable antiroute

# Manage service
systemctl --user start antiroute
systemctl --user status antiroute
systemctl --user stop antiroute
```

---

## License

This project is released under the [MIT License](LICENSE).
