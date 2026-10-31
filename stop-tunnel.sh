#!/usr/bin/env bash
# ==============================================================================
# Stop AntiRoute HTTPS Tunnel
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/tunnel.pid"

if [[ -f "${PID_FILE}" ]]; then
    PID="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${PID}" ]] && ps -p "${PID}" >/dev/null 2>&1; then
        kill -15 "${PID}" 2>/dev/null || kill -9 "${PID}" 2>/dev/null || true
        echo "Tunnel process (PID ${PID}) stopped."
    else
        echo "Tunnel is not running."
    fi
    rm -f "${PID_FILE}" "${SCRIPT_DIR}/tunnel.url"
else
    echo "No tunnel PID file found."
fi
