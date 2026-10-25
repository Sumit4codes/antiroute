#!/usr/bin/env bash
# ==============================================================================
# Test Antigravity Gemini via CLIProxyAPI Anthropic Endpoint
# ==============================================================================
set -euo pipefail

MODEL="${1:-claude-3-7-sonnet-20250219}"

echo "Testing Anthropic Messages API on http://127.0.0.1:8317/v1/messages"
echo "Target Model: ${MODEL} (routed to Antigravity)"
echo "Sending test prompt..."
echo ""

curl -s -X POST "http://127.0.0.1:8317/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-antigravity-claude" \
  -H "anthropic-version: 2023-06-01" \
  -d "{
    \"model\": \"${MODEL}\",
    \"max_tokens\": 100,
    \"messages\": [
      {\"role\": \"user\", \"content\": \"Say hello from Claude Code in 5 words.\"}
    ]
  }" | jq . || true
echo ""
