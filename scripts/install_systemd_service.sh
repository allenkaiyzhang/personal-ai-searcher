#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-personal-ai-searcher}"
SERVICE_FILE="${SERVICE_FILE:-/etc/systemd/system/${SERVICE_NAME}.service}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_SERVICE="$PROJECT_ROOT/systemd/${SERVICE_NAME}.service"

echo "==> Installing systemd service for personal-ai-searcher"
echo "==> Project root: $PROJECT_ROOT"
echo "==> Service name: $SERVICE_NAME"
echo "==> Service file: $SERVICE_FILE"

if [ ! -f "$SOURCE_SERVICE" ]; then
  echo "ERROR: systemd service file not found: $SOURCE_SERVICE" >&2
  exit 1
fi

echo "==> Copying service file"
sudo cp "$SOURCE_SERVICE" "$SERVICE_FILE"

echo "==> Reloading systemd"
sudo systemctl daemon-reload

echo "==> Enabling service"
sudo systemctl enable "$SERVICE_NAME"

echo "==> Service installed successfully"
echo "==> Start it with:"
echo "    sudo systemctl start $SERVICE_NAME"
echo "==> Or deploy and restart it with:"
echo "    scripts/deploy.sh"
