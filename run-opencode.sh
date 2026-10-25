#!/usr/bin/env bash
# ==============================================================================
# Launcher for OpenCode via Antigravity Gemini Proxy
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure proxy is running
if ! curl -s "http://127.0.0.1:8317/" > /dev/null 2>&1; then
    echo "Antigravity Proxy is not running. Starting proxy first..."
    "${SCRIPT_DIR}/start-proxy.sh"
fi

# Export connection parameters
export OPENAI_BASE_URL="http://127.0.0.1:8317/v1"
export OPENAI_API_KEY="sk-antigravity-claude"
export ANTHROPIC_BASE_URL="http://127.0.0.1:8317"
export ANTHROPIC_API_KEY="sk-antigravity-claude"
export OPENCODE_MODEL="antigravity/gemini-3.8-flash-high"

echo "Starting OpenCode connected to Antigravity Proxy..."
if command -v opencode >/dev/null 2>&1; then
    exec opencode "$@"
elif command -v npx >/dev/null 2>&1; then
    exec npx opencode "$@"
else
    echo "Error: opencode command not found. Install it via: npm i -g opencode"
    exit 1
fi