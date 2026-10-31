#!/usr/bin/env bash
# ==============================================================================
# AntiRoute - Public HTTPS Tunnel for Android & Remote Smartphone Access
# Solves Android "cleartext HTTP traffic not permitted" by providing a live HTTPS endpoint.
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
cd "${SCRIPT_DIR}"

# Check for stop argument
if [[ "${1:-}" == "stop" || "${1:-}" == "--stop" || "${1:-}" == "-k" ]]; then
    exec "${SCRIPT_DIR}/stop-tunnel.sh"
fi

TUNNEL_PID_FILE="${SCRIPT_DIR}/tunnel.pid"
TUNNEL_LOG_FILE="${SCRIPT_DIR}/tunnel.log"
TUNNEL_URL_FILE="${SCRIPT_DIR}/tunnel.url"

# Stop existing tunnel if running
if [[ -f "${TUNNEL_PID_FILE}" ]]; then
    OLD_PID="$(cat "${TUNNEL_PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${OLD_PID}" ]] && ps -p "${OLD_PID}" >/dev/null 2>&1; then
        echo "Stopping previous tunnel (PID ${OLD_PID})..."
        kill -15 "${OLD_PID}" 2>/dev/null || kill -9 "${OLD_PID}" 2>/dev/null || true
        sleep 1
    fi
    rm -f "${TUNNEL_PID_FILE}"
fi

# Ensure core proxy is running
if ! curl -s http://127.0.0.1:8317/ >/dev/null 2>&1; then
    echo "Starting AntiRoute proxy..."
    systemctl --user start antiroute 2>/dev/null || ./start-proxy.sh >/dev/null 2>&1 || true
    sleep 2
fi

echo "Launching secure HTTPS tunnel via SSH..."
> "${TUNNEL_LOG_FILE}"

# Start Pinggy SSH tunnel in background
nohup ssh -o StrictHostKeyChecking=no \
          -o ServerAliveInterval=30 \
          -o ServerAliveCountMax=3 \
          -o ExitOnForwardFailure=yes \
          -p 443 -R0:localhost:8317 a.pinggy.io \
          > "${TUNNEL_LOG_FILE}" 2>&1 &

TUNNEL_PID=$!
echo "${TUNNEL_PID}" > "${TUNNEL_PID_FILE}"
disown "${TUNNEL_PID}" 2>/dev/null || true

# Wait for HTTPS URL to appear in log
HTTPS_URL=""
for _ in {1..25}; do
    sleep 0.5
    if grep -E -o "https://[a-zA-Z0-9.-]+\.pinggy[-a-z0-9.]*" "${TUNNEL_LOG_FILE}" >/dev/null 2>&1; then
        HTTPS_URL="$(grep -E -o "https://[a-zA-Z0-9.-]+\.pinggy[-a-z0-9.]*" "${TUNNEL_LOG_FILE}" | grep "free" | head -n 1)"
        if [[ -z "${HTTPS_URL}" ]]; then
            HTTPS_URL="$(grep -E -o "https://[a-zA-Z0-9.-]+\.pinggy[-a-z0-9.]*" "${TUNNEL_LOG_FILE}" | head -n 1)"
        fi
        echo "${HTTPS_URL}" > "${TUNNEL_URL_FILE}"
        break
    fi
done

if [[ -z "${HTTPS_URL}" ]]; then
    echo "Tunnel started with PID ${TUNNEL_PID}, but URL not detected yet. Check ${TUNNEL_LOG_FILE}."
    exit 1
fi

echo ""
echo "=================================================================="
echo " ✦ AntiRoute Secure HTTPS Tunnel Active ✦"
echo "=================================================================="
echo "• HTTPS Base URL:     ${HTTPS_URL}/v1"
echo "• Chat Completions:   ${HTTPS_URL}/v1/chat/completions"
echo "• Models Catalog:     ${HTTPS_URL}/v1/models"
echo "• API Key:            sk-antigravity-claude"
echo "• Model:              gemini-3.8-flash-high"
echo "=================================================================="
echo ""
echo "📱 Configuration for Koda Dev (code_agent) Android App:"
echo "   1. Base URL / API Host: ${HTTPS_URL}/v1"
echo "   2. API Key:             sk-antigravity-claude"
echo "   3. Model:               gemini-3.8-flash-high"
echo ""
echo "✔ Using HTTPS avoids Android's 'cleartext HTTP traffic not permitted' error!"
echo "=================================================================="

# Optional ASCII QR Code
python3 -c "import sys; sys.path.insert(0, '${SCRIPT_DIR}'); import mobile_server; mobile_server.print_ascii_qr('${HTTPS_URL}')" 2>/dev/null || true
