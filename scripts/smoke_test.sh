#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_ROOT/.env" ]; then
  echo "==> Loading environment from $PROJECT_ROOT/.env"
  set -a
  . "$PROJECT_ROOT/.env"
  set +a
else
  echo "==> No .env file found at $PROJECT_ROOT/.env"
fi

if [ "${DEEPSEEK_API_KEY:-}" ]; then
  echo "==> DEEPSEEK_API_KEY is set"
else
  echo "==> DEEPSEEK_API_KEY is unset"
fi
echo "==> ENABLE_QUERY_REWRITE=${ENABLE_QUERY_REWRITE:-0}"

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "==> Checking health endpoint"
curl -fsS "$BASE_URL/health" >/dev/null

echo "==> Checking search endpoint"
SEARCH_RESPONSE="$(curl -fsS \
  -H "Content-Type: application/json" \
  -d '{"query":"OpenAI API web search","max_results":5,"market":"en-US","rewrite_query":false}' \
  "$BASE_URL/search")"

printf '%s' "$SEARCH_RESPONSE" | grep '"results"' >/dev/null

echo "==> Checking search URL normalization"
VAT_SEARCH_RESPONSE="$(curl -fsS \
  -H "Content-Type: application/json" \
  -d '{"query":"VAT Chinese translation","max_results":5,"market":"en-US"}' \
  "$BASE_URL/search")"

VAT_FIRST_URL="$(printf '%s' "$VAT_SEARCH_RESPONSE" | python3 -c 'import json,sys; data=json.load(sys.stdin); results=data.get("results", []); print(results[0].get("url", "") if results else "")')"

if [ -z "$VAT_FIRST_URL" ]; then
  echo "==> Warning: VAT search returned no results; skipping URL normalization assertion"
elif printf '%s' "$VAT_FIRST_URL" | grep 'bing.com/ck/a' >/dev/null; then
  echo "==> Search URL normalization failed: $VAT_FIRST_URL" >&2
  exit 1
else
  echo "==> Search URL normalization check passed"
fi

if [ "${DEEPSEEK_API_KEY:-}" ] && [ "${ENABLE_QUERY_REWRITE:-0}" = "1" ]; then
  echo "==> Checking search endpoint with query rewrite"
  if REWRITE_RESPONSE="$(curl -fsS \
    -H "Content-Type: application/json" \
    -d '{"query":"How to speak VAT in CHinese","max_results":5,"market":"en-US","rewrite_query":true}' \
    "$BASE_URL/search")"; then
    printf '%s' "$REWRITE_RESPONSE" | grep '"rewritten_queries"' >/dev/null
    echo "==> Query rewrite smoke check passed"
  else
    echo "==> Warning: query rewrite smoke check failed; continuing because external LLM access is optional"
  fi
else
  echo "==> Skipping query rewrite smoke check because DEEPSEEK_API_KEY is empty or ENABLE_QUERY_REWRITE is not 1"
fi

echo "==> Smoke test completed successfully"
