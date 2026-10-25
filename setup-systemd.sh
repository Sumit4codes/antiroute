#!/usr/bin/env bash
# ==============================================================================
# Setup systemd user service for AntiRoute Daemon
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_FILE="${SERVICE_DIR}/antiroute.service"

ACTION="${1:-install}"

case "${ACTION}" in
    install|enable)
        mkdir -p "${SERVICE_DIR}"
        cat <<EOF > "${SERVICE_FILE}"
[Unit]
Description=AntiRoute - Antigravity AI Agent Router Daemon
After=network.target

[Service]
Type=simple
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/cli-proxy-api -config ${SCRIPT_DIR}/config.yaml
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
EOF

        # Maintain backwards-compatible symlink
        ln -sf "${SERVICE_FILE}" "${SERVICE_DIR}/gemini-proxy.service"

        systemctl --user daemon-reload
        echo "=================================================================="
        echo " ✦ AntiRoute Systemd Service Installed: ${SERVICE_FILE} ✦"
        echo "=================================================================="
        echo "To enable on login:"
        echo "  systemctl --user enable antiroute"
        echo ""
        echo "To start now via systemd:"
        echo "  ./stop-proxy.sh  # stop any existing manual instance first"
        echo "  systemctl --user start antiroute"
        echo ""
        echo "To check status:"
        echo "  systemctl --user status antiroute"
        echo "=================================================================="
        ;;
    uninstall|disable)
        systemctl --user stop antiroute 2>/dev/null || true
        systemctl --user disable antiroute 2>/dev/null || true
        rm -f "${SERVICE_FILE}" "${SERVICE_DIR}/gemini-proxy.service"
        systemctl --user daemon-reload
        echo "AntiRoute systemd service removed."
        ;;
    *)
        echo "Usage: ./setup-systemd.sh [install|uninstall]"
        exit 1
        ;;
esac
