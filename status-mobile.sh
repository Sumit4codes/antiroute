#!/usr/bin/env bash
# ==============================================================================
# Check AntiRoute Mobile Gateway Status
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
PYTHON_BIN="$(command -v python3 || echo "/usr/bin/python3")"

"${PYTHON_BIN}" "${SCRIPT_DIR}/mobile_server.py" --status
