#!/usr/bin/env bash
# ==============================================================================
# Run Claude Code with Antigravity Gemini
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure proxy is running
if ! curl -s --connect-timeout 2 http://127.0.0.1:8317/ > /dev/null 2>&1; then
    echo "CLIProxyAPI is not currently running. Starting it now..."
    "${SCRIPT_DIR}/start-proxy.sh"
fi

# Check for claude binary
CLAUDE_BIN="$(command -v claude 2>/dev/null || echo "")"
if [[ -z "${CLAUDE_BIN}" ]]; then
    if [[ -x "/home/sumit/.npm-global/bin/claude" ]]; then
        CLAUDE_BIN="/home/sumit/.npm-global/bin/claude"
    else
        echo "Error: 'claude' CLI command not found in PATH."
        echo "Install it via: npm install -g @anthropic-ai/claude-code"
        exit 1
    fi
fi

# Check for cached Anthropic credentials that may override the custom gateway
CREDS_FILE="${HOME}/.claude/.credentials.json"
if [[ -f "${CREDS_FILE}" ]]; then
    echo "Notice: Detected '${CREDS_FILE}'."
    echo "If Claude fails with authentication errors, run '/logout' inside Claude Code or remove ~/.claude/.credentials.json."
fi

# Configure environment variables for Claude Code
export ANTHROPIC_BASE_URL="http://127.0.0.1:8317"
export ANTHROPIC_API_KEY="sk-antigravity-claude"
unset ANTHROPIC_AUTH_TOKEN

# Model configuration:
# Default to claude-3-7-sonnet-20250219 so Claude Code operates without unrecognized model warnings,
# which the proxy maps directly to Antigravity's Gemini 3.8 Flash (High) thinking model.
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-3-7-sonnet-20250219}"

echo "=================================================================="
echo " Launching Claude Code with Antigravity Gemini"
echo " Base URL : ${ANTHROPIC_BASE_URL}"
echo " Model    : ${ANTHROPIC_MODEL} (mapped to Antigravity Gemini)"
echo "=================================================================="

exec "${CLAUDE_BIN}" "$@"
