#!/usr/bin/env bash
# ==============================================================================
# Login to Google Antigravity OAuth for CLIProxyAPI
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.yaml"
BINARY="${SCRIPT_DIR}/cli-proxy-api"

if [[ ! -x "${BINARY}" ]]; then
    chmod +x "${BINARY}"
fi

echo "=================================================================="
echo " Google Antigravity OAuth Login"
echo "=================================================================="
echo "This will start the OAuth flow for your Google Antigravity account."
echo "Tokens will be saved in: ${SCRIPT_DIR}/.auth"
echo ""

# Check for display/browser
NO_BROWSER_FLAG=""
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    echo "No graphical display detected; enabling --no-browser mode."
    NO_BROWSER_FLAG="-no-browser"
fi

if [[ "${1:-}" == "--no-browser" ]]; then
    NO_BROWSER_FLAG="-no-browser"
fi

"${BINARY}" -config "${CONFIG_FILE}" -antigravity-login ${NO_BROWSER_FLAG}
