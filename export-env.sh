#!/usr/bin/env bash
# ==============================================================================
# AntiRoute - Shell Environment Exporter
# Usage: source ./export-env.sh [opencode|hermes|claude|aider|goose|droid]
# ==============================================================================

TOOL="${1:-hermes}"

case "${TOOL}" in
    opencode|open-code)
        export OPENAI_BASE_URL="http://127.0.0.1:8317/v1"
        export OPENAI_API_KEY="sk-antigravity-claude"
        export ANTHROPIC_BASE_URL="http://127.0.0.1:8317"
        export ANTHROPIC_API_KEY="sk-antigravity-claude"
        export MODEL="gemini-3.8-flash-high"
        echo "✔ OpenCode environment configured (OpenAI & Anthropic formats)."
        ;;
    hermes|hermes-agent|nous-hermes)
        export OPENAI_BASE_URL="http://127.0.0.1:8317/v1"
        export OPENAI_API_KEY="sk-antigravity-claude"
        export MODEL="gemini-3.8-flash-high"
        echo "✔ Hermes Agent environment configured (OPENAI_BASE_URL=http://127.0.0.1:8317/v1)."
        ;;
    claude|claude-code)
        export ANTHROPIC_BASE_URL="http://127.0.0.1:8317"
        export ANTHROPIC_API_KEY="sk-antigravity-claude"
        echo "✔ Claude Code environment configured (ANTHROPIC_BASE_URL=http://127.0.0.1:8317)."
        ;;
    aider)
        export OPENAI_API_BASE="http://127.0.0.1:8317/v1"
        export OPENAI_API_KEY="sk-antigravity-claude"
        echo "✔ Aider environment configured (OPENAI_API_BASE=http://127.0.0.1:8317/v1)."
        ;;
    goose)
        export OPENAI_BASE_URL="http://127.0.0.1:8317/v1"
        export OPENAI_API_KEY="sk-antigravity-claude"
        export GOOSE_PROVIDER="openai"
        export GOOSE_MODEL="gemini-3.8-flash-high"
        echo "✔ Goose environment configured (OPENAI_BASE_URL=http://127.0.0.1:8317/v1)."
        ;;
    droid)
        export OPENAI_BASE_URL="http://127.0.0.1:8317/v1"
        export OPENAI_API_KEY="sk-antigravity-claude"
        export ANTHROPIC_BASE_URL="http://127.0.0.1:8317"
        export ANTHROPIC_API_KEY="sk-antigravity-claude"
        echo "✔ Droid environment configured (OPENAI & Anthropic endpoints)."
        ;;
    *)
        echo "Unknown tool: ${TOOL}"
        echo "Available tools: opencode, hermes, claude, aider, goose, droid"
        return 1 2>/dev/null || exit 1
        ;;
esac
