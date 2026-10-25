#!/usr/bin/env bash
# ==============================================================================
# Stop CLIProxyAPI Daemon
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/proxy.pid"

if [[ -f "${PID_FILE}" ]]; then
    PID="$(cat "${PID_FILE}")"
    if ps -p "${PID}" > /dev/null 2>&1; then
        echo "Stopping CLIProxyAPI (PID: ${PID})..."
        kill "${PID}" || true
        for _ in {1..10}; do
            if ! ps -p "${PID}" > /dev/null 2>&1; then
                break
            fi
            sleep 0.5
        done
        if ps -p "${PID}" > /dev/null 2>&1; then
            echo "Force killing PID: ${PID}..."
            kill -9 "${PID}" || true
        fi
        echo "Proxy stopped."
    else
        echo "No running process found for PID ${PID}."
    fi
    rm -f "${PID_FILE}"
else
    # Check if any cli-proxy-api is running
    PIDS="$(pgrep -f "cli-proxy-api.*config" || true)"
    if [[ -n "${PIDS}" ]]; then
        echo "Stopping cli-proxy-api processes: ${PIDS}"
        kill ${PIDS} || true
        echo "Stopped."
    else
        echo "CLIProxyAPI is not running."
    fi
fi
