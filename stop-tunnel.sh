#!/usr/bin/env bash
# ==============================================================================
# Stop AntiRoute HTTPS Tunnel
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
PID_FILE="${SCRIPT_DIR}/tunnel.pid"

STOPPED=false

if [[ -f "${PID_FILE}" ]]; then
    PID="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${PID}" ]] && ps -p "${PID}" >/dev/null 2>&1; then
        kill -15 "${PID}" 2>/dev/null || kill -9 "${PID}" 2>/dev/null || true
        echo "✔ AntiRoute HTTPS Tunnel (PID ${PID}) stopped."
        STOPPED=true
    fi
    rm -f "${PID_FILE}" "${SCRIPT_DIR}/tunnel.url"
fi

# Fallback: check and terminate any lingering pinggy/localhost.run forwarders for 8317
LINGERING_PIDS="$(pgrep -f "ssh.*(a\.pinggy\.io|localhost\.run).*8317" || true)"
if [[ -n "${LINGERING_PIDS}" ]]; then
    for p in ${LINGERING_PIDS}; do
        kill -15 "${p}" 2>/dev/null || kill -9 "${p}" 2>/dev/null || true
    done
    echo "✔ Cleaned up lingering tunnel process(es)."
    STOPPED=true
fi

if [[ "${STOPPED}" == "false" ]]; then
    echo "AntiRoute HTTPS Tunnel is not running."
fi
