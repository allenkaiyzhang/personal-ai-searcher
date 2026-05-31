#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-personal-ai-searcher}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
LOG_FILE="$PROJECT_ROOT/deploy.log"
SERVICE_FILE="$PROJECT_ROOT/systemd/${SERVICE_NAME}.service"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8020/health}"

mkdir -p "$PROJECT_ROOT/data" "$PROJECT_ROOT/logs"
touch "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

cd "$PROJECT_ROOT"

echo "==> Deploying $SERVICE_NAME from $PROJECT_ROOT"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
  echo "ERROR: $PROJECT_ROOT/.env is required. Create it from .env.example before deploying." >&2
  exit 1
fi

if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
  echo "ERROR: requirements.txt is required." >&2
  exit 1
fi

if [ ! -f "$SERVICE_FILE" ]; then
  echo "ERROR: systemd service file not found: $SERVICE_FILE" >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "==> Creating virtual environment"
  python3 -m venv "$VENV_DIR"
fi

echo "==> Upgrading pip"
"$VENV_DIR/bin/python" -m pip install -U pip

echo "==> Installing dependencies"
"$VENV_DIR/bin/python" -m pip install -r "$PROJECT_ROOT/requirements.txt"

echo "==> Initializing database"
"$VENV_DIR/bin/python" -m app.db.init_db

echo "==> Installing systemd unit"
sudo cp "$SERVICE_FILE" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "==> Waiting for service startup"
sleep 2

sudo systemctl --no-pager --full status "$SERVICE_NAME" || true

HEALTH_URL="$HEALTH_URL" "$SCRIPT_DIR/smoke_test.sh"

echo "==> Deployment finished"
