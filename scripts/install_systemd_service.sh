#!/usr/bin/env sh
set -eu

SERVICE_NAME="${SERVICE_NAME:-personal-ai-searcher}"
SERVICE_FILE="${SERVICE_FILE:-/etc/systemd/system/${SERVICE_NAME}.service}"
HOST_ADDRESS="${HOST_ADDRESS:-127.0.0.1}"
PORT="${PORT:-8000}"

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
TMP_SERVICE="$(mktemp)"

cleanup() {
  rm -f "$TMP_SERVICE"
}
trap cleanup EXIT

echo "==> Installing systemd service for personal-AI-searcher"
echo "==> Project root: $PROJECT_ROOT"
echo "==> Service name: $SERVICE_NAME"
echo "==> Service file: $SERVICE_FILE"
echo "==> Service host: $HOST_ADDRESS"
echo "==> Service port: $PORT"

cat > "$TMP_SERVICE" <<EOF
[Unit]
Description=Personal AI Searcher
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_ROOT
ExecStart=$VENV_PYTHON -m uvicorn app.main:app --host $HOST_ADDRESS --port $PORT
Restart=always
RestartSec=5
EnvironmentFile=-$PROJECT_ROOT/.env
Environment=DATABASE_URL=sqlite:///./data/searcher.db
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "==> Copying service file"
sudo cp "$TMP_SERVICE" "$SERVICE_FILE"

echo "==> Reloading systemd"
sudo systemctl daemon-reload

echo "==> Enabling service"
sudo systemctl enable "$SERVICE_NAME"

echo "==> Service installed successfully"
echo "==> Start it with:"
echo "    sudo systemctl start $SERVICE_NAME"
echo "==> Or deploy and restart it with:"
echo "    scripts/deploy.sh"
