#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-personal-ai-searcher}"
LINES="${LINES:-120}"

sudo journalctl -u "$SERVICE_NAME" -n "$LINES" --no-pager
