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
if [ "${API_KEY:-}" ]; then
  echo "==> API_KEY is set"
else
  echo "==> API_KEY is not set"
fi
echo "==> ENABLE_QUERY_REWRITE=${ENABLE_QUERY_REWRITE:-0}"

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

api_post() {
  path="$1"
  body="$2"
  if [ "${API_KEY:-}" ]; then
    curl -fsS \
      -H "Content-Type: application/json" \
      -H "X-API-Key: $API_KEY" \
      -d "$body" \
      "$BASE_URL$path"
  else
    curl -fsS \
      -H "Content-Type: application/json" \
      -d "$body" \
      "$BASE_URL$path"
  fi
}

echo "==> Checking health endpoint"
curl -fsS "$BASE_URL/health" >/dev/null

if [ "${API_KEY:-}" ]; then
  echo "==> Checking API key protection rejects missing key"
  STATUS_CODE="$(curl -sS -o /dev/null -w '%{http_code}' \
    -H "Content-Type: application/json" \
    -d '{"query":"OpenAI API web search","max_results":1,"market":"en-US","rewrite_query":false}' \
    "$BASE_URL/search")"
  if [ "$STATUS_CODE" != "401" ]; then
    echo "==> Expected /search without X-API-Key to return 401, got $STATUS_CODE" >&2
    exit 1
  fi
fi

echo "==> Checking search endpoint"
SEARCH_RESPONSE="$(api_post "/search" '{"query":"OpenAI API web search","max_results":5,"market":"en-US","rewrite_query":false}')"

printf '%s' "$SEARCH_RESPONSE" | grep '"results"' >/dev/null

if [ "${API_KEY:-}" ]; then
  echo "==> Checking API key protection accepts configured key"
fi

echo "==> Checking search URL normalization"
VAT_SEARCH_RESPONSE="$(api_post "/search" '{"query":"VAT Chinese translation","max_results":5,"market":"en-US"}')"

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
  if REWRITE_RESPONSE="$(api_post "/search" '{"query":"How to speak VAT in CHinese","max_results":5,"market":"en-US","rewrite_query":true}')"; then
    printf '%s' "$REWRITE_RESPONSE" | grep '"rewritten_queries"' >/dev/null
    echo "==> Query rewrite smoke check passed"
  else
    echo "==> Warning: query rewrite smoke check failed; continuing because external LLM access is optional"
  fi
else
  echo "==> Skipping query rewrite smoke check because DEEPSEEK_API_KEY is empty or ENABLE_QUERY_REWRITE is not 1"
fi

echo "==> Smoke test completed successfully"
