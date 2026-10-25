#!/usr/bin/env bash
# ==============================================================================
# Install AntiRoute CLI & TUI shortcuts into ~/.local/bin
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

mkdir -p "${BIN_DIR}"

# Primary AntiRoute commands
ln -sf "${SCRIPT_DIR}/antiroute" "${BIN_DIR}/antiroute"
ln -sf "${SCRIPT_DIR}/run-hermes.sh" "${BIN_DIR}/antiroute-hermes"
ln -sf "${SCRIPT_DIR}/run-opencode.sh" "${BIN_DIR}/antiroute-opencode"
ln -sf "${SCRIPT_DIR}/run-claude.sh" "${BIN_DIR}/antiroute-claude"

# Compatibility symlinks
ln -sf "${SCRIPT_DIR}/antiroute" "${BIN_DIR}/antigravity-tui"
ln -sf "${SCRIPT_DIR}/antiroute" "${BIN_DIR}/gemini-proxy"
ln -sf "${SCRIPT_DIR}/run-hermes.sh" "${BIN_DIR}/run-hermes-gemini"
ln -sf "${SCRIPT_DIR}/run-opencode.sh" "${BIN_DIR}/run-opencode-gemini"
ln -sf "${SCRIPT_DIR}/run-claude.sh" "${BIN_DIR}/run-claude-gemini"

# Auto-configure OpenCode and Hermes if available
python3 -c "import sys; sys.path.insert(0, '${SCRIPT_DIR}'); import proxy_manager as pm; pm.configure_opencode(); pm.configure_hermes()" 2>/dev/null || true

echo "=================================================================="
echo " ✦ AntiRoute CLI & TUI Successfully Installed! ✦"
echo "=================================================================="
echo "Commands available in ${BIN_DIR}:"
echo "  • antiroute            -> Launch AntiRoute TUI or CLI"
echo "  • antiroute status     -> Check router health & accounts"
echo "  • antiroute-hermes     -> Launch Hermes Agent via Gemini"
echo "  • antiroute-opencode   -> Launch OpenCode via Gemini"
echo "  • antiroute-claude     -> Launch Claude Code via Gemini"
echo ""
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo "Notice: ${BIN_DIR} is not currently in your PATH."
    echo "Add it by adding this line to your ~/.zshrc or ~/.bashrc:"
    # shellcheck disable=SC2016
    echo '  export PATH="$HOME/.local/bin:$PATH"'
fi
echo "=================================================================="
