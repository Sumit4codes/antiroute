#!/usr/bin/env bash
# ==============================================================================
# Launcher for Hermes Agent via AntiRoute (Gemini Antigravity)
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
    echo "AntiRoute is not running. Starting proxy first..."
    "${SCRIPT_DIR}/start-proxy.sh"
fi

# Ensure Hermes config has antiroute custom provider registered
python3 -c "import sys; sys.path.insert(0, '${SCRIPT_DIR}'); import proxy_manager as pm; pm.configure_hermes()" 2>/dev/null || true

# Export connection parameters
export OPENAI_BASE_URL="http://127.0.0.1:8317/v1"
export OPENAI_API_KEY="sk-antigravity-claude"
export CUSTOM_BASE_URL="http://127.0.0.1:8317/v1"
export HERMES_INFERENCE_PROVIDER="custom:antiroute"
export HERMES_INFERENCE_MODEL="gemini-3.8-flash-high"

echo "=================================================================="
echo " Starting Hermes Agent with Antigravity Gemini"
echo " Base URL : ${OPENAI_BASE_URL}"
echo " Model    : gemini-3.8-flash-high (Antigravity)"
echo " Provider : custom:antiroute"
echo "=================================================================="

# Check if user already provided --provider or -m
EXTRA_ARGS=()
HAS_PROVIDER=0
HAS_MODEL=0
for arg in "$@"; do
    if [[ "${arg}" == "--provider" || "${arg}" == --provider=* ]]; then
        HAS_PROVIDER=1
    fi
    if [[ "${arg}" == "-m" || "${arg}" == "--model" || "${arg}" == --model=* ]]; then
        HAS_MODEL=1
    fi
done

if [[ ${HAS_PROVIDER} -eq 0 ]]; then
    EXTRA_ARGS+=("--provider" "custom:antiroute")
fi
if [[ ${HAS_MODEL} -eq 0 ]]; then
    EXTRA_ARGS+=("-m" "gemini-3.8-flash-high")
fi

if command -v hermes >/dev/null 2>&1; then
    exec hermes "${EXTRA_ARGS[@]}" "$@"
elif [[ -x "${HOME}/.local/bin/hermes" ]]; then
    exec "${HOME}/.local/bin/hermes" "${EXTRA_ARGS[@]}" "$@"
else
    echo "Error: hermes command not found."
    echo "Make sure hermes is installed in your python environment."
    exit 1
fi
