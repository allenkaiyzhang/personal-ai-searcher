#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "==> Checking health endpoint"
curl -fsS "$BASE_URL/health" >/dev/null

echo "==> Checking search endpoint"
SEARCH_RESPONSE="$(curl -fsS \
  -H "Content-Type: application/json" \
  -d '{"query":"OpenAI API web search","max_results":5,"market":"en-US"}' \
  "$BASE_URL/search")"

printf '%s' "$SEARCH_RESPONSE" | grep '"results"' >/dev/null

echo "==> Smoke test completed successfully"
