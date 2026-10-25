#!/usr/bin/env bash
# ==============================================================================
# Check CLIProxyAPI and Antigravity Status
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/proxy.pid"
AUTH_DIR="${SCRIPT_DIR}/.auth"

echo "=================================================================="
echo " CLIProxyAPI & Antigravity Status"
echo "=================================================================="

# Check Process
if [[ -f "${PID_FILE}" ]] && ps -p "$(cat "${PID_FILE}")" > /dev/null 2>&1; then
    echo "• Service Status: RUNNING (PID: $(cat "${PID_FILE}"))"
else
    PIDS="$(pgrep -f "cli-proxy-api.*config" || true)"
    if [[ -n "${PIDS}" ]]; then
        echo "• Service Status: RUNNING (PID: ${PIDS})"
    else
        echo "• Service Status: STOPPED"
    fi
fi

# Check HTTP Endpoint
echo -n "• Health Check (http://127.0.0.1:8317/): "
if HEALTH="$(curl -s --connect-timeout 2 http://127.0.0.1:8317/ 2>/dev/null)"; then
    echo "OK"
    echo "  Response: ${HEALTH}"
else
    echo "OFFLINE / UNREACHABLE"
fi

# Check Antigravity Auth Tokens
echo ""
echo "• Antigravity OAuth Tokens in ${AUTH_DIR}:"
if [[ -d "${AUTH_DIR}" ]]; then
    FILES="$(find "${AUTH_DIR}" -type f -name "*.json" 2>/dev/null || true)"
    if [[ -n "${FILES}" ]]; then
        for f in ${FILES}; do
            echo "  - $(basename "${f}")"
        done
    else
        echo "  - None found. Run './login-antigravity.sh' to authenticate."
    fi
else
    echo "  - Auth directory not found."
fi

echo "=================================================================="
