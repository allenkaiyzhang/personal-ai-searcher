#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-personal-ai-searcher}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8020/health}"

for attempt in $(seq 1 10); do
  echo "==> Smoke test attempt ${attempt}: $HEALTH_URL"
  if curl -fsS --max-time 5 "$HEALTH_URL"; then
    echo
    echo "Smoke test passed"
    exit 0
  fi
  sleep 2
done

echo "Smoke test failed" >&2
sudo systemctl --no-pager --full status "$SERVICE_NAME" || true
sudo journalctl -u "$SERVICE_NAME" -n 100 --no-pager || true
exit 1
