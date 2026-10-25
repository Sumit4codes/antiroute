#!/usr/bin/env bash
# ==============================================================================
# Launcher for Hermes Agent via Antigravity Gemini Proxy
# ==============================================================================
set -euo pipefail

# Resolve symlinks to find real script directory
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

# Ensure proxy is running
if ! curl -s "http://127.0.0.1:8317/" > /dev/null 2>&1; then
    echo "Antigravity Proxy is not running. Starting proxy first..."
    "${SCRIPT_DIR}/start-proxy.sh"
fi

# Export connection parameters
export OPENAI_BASE_URL="http://127.0.0.1:8317/v1"
export OPENAI_API_KEY="sk-antigravity-claude"
export MODEL="gemini-3.8-flash-high"

echo "Starting Hermes Agent connected to Antigravity Proxy..."
if command -v hermes >/dev/null 2>&1; then
    exec hermes "$@"
else
    echo "Error: hermes command not found."
    echo "Make sure hermes is installed in your python environment (e.g. pip install hermes-agent)"
    exit 1
fi
