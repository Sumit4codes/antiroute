#!/usr/bin/env bash
# ==============================================================================
# Start CLIProxyAPI Background Daemon
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.yaml"
BINARY="${SCRIPT_DIR}/cli-proxy-api"
LOG_FILE="${SCRIPT_DIR}/proxy.log"
PID_FILE="${SCRIPT_DIR}/proxy.pid"

if [[ ! -x "${BINARY}" ]]; then
    chmod +x "${BINARY}"
fi

# Check if already running
if [[ -f "${PID_FILE}" ]]; then
    PID="$(cat "${PID_FILE}")"
    if ps -p "${PID}" > /dev/null 2>&1; then
        echo "CLIProxyAPI is already running (PID: ${PID})."
        echo "Use ./stop-proxy.sh to stop it or ./status-proxy.sh to check health."
        exit 0
    else
        rm -f "${PID_FILE}"
    fi
fi

# Foreground mode check
if [[ "${1:-}" == "-f" || "${1:-}" == "--foreground" ]]; then
    echo "Starting CLIProxyAPI in foreground..."
    exec "${BINARY}" -config "${CONFIG_FILE}"
fi

echo "Starting CLIProxyAPI proxy server..."
nohup "${BINARY}" -config "${CONFIG_FILE}" </dev/null > "${LOG_FILE}" 2>&1 &
PID=$!
disown ${PID} 2>/dev/null || true
echo "${PID}" > "${PID_FILE}"

echo "Proxy started with PID ${PID}."
echo "Waiting for server to become ready on http://127.0.0.1:8317..."

for i in {1..15}; do
    if curl -s http://127.0.0.1:8317/ > /dev/null 2>&1; then
        echo ""
        echo "=================================================================="
        echo " SUCCESS: CLIProxyAPI is running on http://127.0.0.1:8317"
        echo " Log file: ${LOG_FILE}"
        echo " Run './run-claude.sh' to start Claude Code with Antigravity!"
        echo "=================================================================="
        exit 0
    fi
    sleep 1
    echo -n "."
done

echo ""
echo "Warning: Proxy started (PID: ${PID}), but health check did not respond yet."
echo "Check '${LOG_FILE}' for details."
