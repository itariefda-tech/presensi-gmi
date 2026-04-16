#!/usr/bin/env bash
set -euo pipefail

# =========================
# CONFIG VPS
# =========================
APP_DIR="/opt/presensi-app"
IMAGE="presensi-app:latest"
CONTAINER="presensi-app"
NETWORK="hosting_web"
PORT="5050"

# Path data di VPS
DATA_DIR="/opt/presensi-app/data"

ENV_FILE="$APP_DIR/.env"
ENV_OPTS=()
if [ -f "$ENV_FILE" ]; then
  ENV_OPTS+=(--env-file "$ENV_FILE")
fi

# =========================
# START
# =========================
cd "$APP_DIR"

echo "==> Git pull"
git pull origin main || true

echo "==> Git status"
git status -sb

echo "==> Git head"
git log -1 --oneline

echo "==> Build image"
docker build --no-cache -t "$IMAGE" .

echo "==> Stop/remove old container (if exists)"
docker stop "$CONTAINER" >/dev/null 2>&1 || true
docker rm "$CONTAINER" >/dev/null 2>&1 || true

echo "==> Ensure network exists"
docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK"

echo "==> Ensure data dir exists"
mkdir -p "$DATA_DIR"
chmod -R 777 "$DATA_DIR"

echo "==> Run new container"
docker run -d --name "$CONTAINER" \
  --user 0:0 \
  --network "$NETWORK" \
  -p "${PORT}:5050" \
  "${ENV_OPTS[@]}" \
  -e FLASK_SECRET="super-secret-$(date +%s)" \
  -e PRESENSI_DB_PATH=/data/presensi.db \
  -v "$DATA_DIR":/data \
  "$IMAGE"

echo "==> Done"
docker ps --filter "name=$CONTAINER"
