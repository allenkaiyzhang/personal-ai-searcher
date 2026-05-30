#!/usr/bin/env sh
set -eu

SERVICE_NAME="${SERVICE_NAME:-personal-ai-searcher}"
HOST_ADDRESS="${HOST_ADDRESS:-127.0.0.1}"
PORT="${PORT:-8000}"
SKIP_TESTS="${SKIP_TESTS:-0}"
NO_RESTART="${NO_RESTART:-0}"
RECREATE_VENV="${RECREATE_VENV:-0}"
UPGRADE_PIP="${UPGRADE_PIP:-0}"
RUN_GIT_PULL="${RUN_GIT_PULL:-0}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://127.0.0.1:${PORT}/health}"

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/.venv"
PYTHON_PATH="$VENV_PATH/bin/python"

cd "$PROJECT_ROOT"

echo "==> Deploying personal-AI-searcher from $PROJECT_ROOT"
echo "==> Service name: $SERVICE_NAME"
echo "==> Service host: $HOST_ADDRESS"
echo "==> Service port: $PORT"

if [ "$RUN_GIT_PULL" = "1" ]; then
  echo "==> Pulling latest code with fast-forward only"
  git pull --ff-only
fi

echo "==> Ensuring data directory exists"
mkdir -p "$PROJECT_ROOT/data"

if [ "$RECREATE_VENV" = "1" ] && [ -d "$VENV_PATH" ]; then
  echo "==> Removing existing virtual environment"
  rm -rf "$VENV_PATH"
fi

if [ ! -x "$PYTHON_PATH" ]; then
  echo "==> Creating virtual environment"
  python3 -m venv "$VENV_PATH"
fi

if [ "$UPGRADE_PIP" = "1" ]; then
  echo "==> Upgrading pip"
  "$PYTHON_PATH" -m pip install --upgrade pip
fi

echo "==> Installing dependencies"
"$PYTHON_PATH" -m pip install -r requirements.txt

if [ "$SKIP_TESTS" != "1" ]; then
  echo "==> Running tests"
  "$PYTHON_PATH" -m pytest
else
  echo "==> Skipping tests because SKIP_TESTS=1"
fi

echo "==> Initializing database"
"$PYTHON_PATH" -m app.db.init_db

if [ "$NO_RESTART" = "1" ]; then
  echo "==> Deployment finished. Service was not restarted because NO_RESTART=1."
  exit 0
fi

echo "==> Restarting systemd service: $SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "==> Waiting for service startup"
sleep 2

echo "==> Running health check: $HEALTHCHECK_URL"
curl -fsS "$HEALTHCHECK_URL" >/dev/null

echo "==> Deployment completed successfully"
