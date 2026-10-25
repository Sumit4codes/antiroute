#!/usr/bin/env bash
# ==============================================================================
# Antigravity Gemini Proxy - Interactive TUI Launcher
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

PYTHON_EXEC="$(command -v python3 || echo "")"

if [[ -z "${PYTHON_EXEC}" ]]; then
    echo "Error: Python 3 is required to run the TUI."
    exit 1
fi

# Ensure cli-proxy-api is executable
if [[ -f "${SCRIPT_DIR}/cli-proxy-api" && ! -x "${SCRIPT_DIR}/cli-proxy-api" ]]; then
    chmod +x "${SCRIPT_DIR}/cli-proxy-api"
fi

exec "${PYTHON_EXEC}" "${SCRIPT_DIR}/tui.py" "$@"
