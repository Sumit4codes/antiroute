#!/usr/bin/env bash
# ==============================================================================
# AntiRoute - Start Mobile Gateway & Smartphone Cockpit
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

PYTHON_BIN="$(command -v python3 || echo "/usr/bin/python3")"

# Ensure core proxy is running
if ! curl -s http://127.0.0.1:8317/ >/dev/null 2>&1; then
    echo "Starting AntiRoute core proxy daemon..."
    ./start-proxy.sh >/dev/null 2>&1 || systemctl --user start antiroute 2>/dev/null || true
    sleep 2
fi

# If systemd service is installed, use systemd to manage it cleanly
if systemctl --user is-enabled antiroute-mobile >/dev/null 2>&1; then
    systemctl --user start antiroute-mobile
fi

# Print ASCII QR code and connection info
"${PYTHON_BIN}" "${SCRIPT_DIR}/mobile_server.py" --qr

PRIMARY_IP="$("${PYTHON_BIN}" -c "import sys; sys.path.insert(0, '${SCRIPT_DIR}'); import mobile_server; print(mobile_server.get_primary_ip())")"

echo "=================================================================="
echo " ✦ AntiRoute Mobile Gateway is Ready! ✦"
echo "=================================================================="
echo "1. Smartphone Web Chat (PWA with Voice):"
echo "   👉 http://${PRIMARY_IP}:8318"
echo ""
echo "2. Smartphone Apps (Chatbox, NextChat):"
echo "   • Base URL: http://${PRIMARY_IP}:8317/v1 (or http://${PRIMARY_IP}:8318/v1)"
echo "   • API Key:  sk-antigravity-claude"
echo "   • Model:    gemini-3.8-flash-high"
echo ""
echo "3. Mobile Setup & Siri Guide:"
echo "   👉 http://${PRIMARY_IP}:8318/setup"
echo "=================================================================="
