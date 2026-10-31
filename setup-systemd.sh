#!/usr/bin/env bash
# ==============================================================================
# Setup systemd user services for AntiRoute Core & Mobile Daemons
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="${HOME}/.config/systemd/user"
CORE_SERVICE="${SERVICE_DIR}/antiroute.service"
MOBILE_SERVICE="${SERVICE_DIR}/antiroute-mobile.service"

ACTION="${1:-install}"
PYTHON_BIN="$(command -v python3 || echo "/usr/bin/python3")"

case "${ACTION}" in
    install|enable)
        mkdir -p "${SERVICE_DIR}"

        # 1. AntiRoute Core Proxy Service
        cat <<EOF > "${CORE_SERVICE}"
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

        # 2. AntiRoute Mobile Gateway & Web Chat Service
        cat <<EOF > "${MOBILE_SERVICE}"
[Unit]
Description=AntiRoute - Mobile Gateway & Smartphone Web Chat
After=network.target antiroute.service
Wants=antiroute.service

[Service]
Type=simple
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${PYTHON_BIN} ${SCRIPT_DIR}/mobile_server.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
EOF

        # Backwards compatibility symlink
        ln -sf "${CORE_SERVICE}" "${SERVICE_DIR}/gemini-proxy.service"

        systemctl --user daemon-reload
        echo "=================================================================="
        echo " ✦ AntiRoute Core & Mobile Systemd Services Installed ✦"
        echo "=================================================================="
        echo "Services installed:"
        echo "  • ${CORE_SERVICE}"
        echo "  • ${MOBILE_SERVICE}"
        echo ""
        echo "To enable both on user login:"
        echo "  systemctl --user enable antiroute antiroute-mobile"
        echo ""
        echo "To start both now:"
        echo "  systemctl --user start antiroute antiroute-mobile"
        echo ""
        echo "To check status:"
        echo "  systemctl --user status antiroute antiroute-mobile"
        echo "=================================================================="
        ;;
    uninstall|disable)
        systemctl --user stop antiroute-mobile antiroute 2>/dev/null || true
        systemctl --user disable antiroute-mobile antiroute 2>/dev/null || true
        rm -f "${CORE_SERVICE}" "${MOBILE_SERVICE}" "${SERVICE_DIR}/gemini-proxy.service"
        systemctl --user daemon-reload
        echo "AntiRoute core and mobile systemd services removed."
        ;;
    *)
        echo "Usage: ./setup-systemd.sh [install|uninstall]"
        exit 1
        ;;
esac
