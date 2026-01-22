#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/mnt/ssd/hosting/presensi-app"
IMAGE="presensi-app:latest"
CONTAINER="presensi-app"
NETWORK="hosting_web"
PORT="5050"
DB_PATH="/mnt/ssd/hosting/presensi-app/presensi.db"

cd "$APP_DIR"

echo "==> Git pull"
git pull origin main

echo "==> Build image"
docker build -t "$IMAGE" .

echo "==> Stop/remove old container (if exists)"
docker stop "$CONTAINER" >/dev/null 2>&1 || true
docker rm "$CONTAINER" >/dev/null 2>&1 || true

echo "==> Run new container"
docker run -d --name "$CONTAINER" \
  --user 0:0 \
  --network "$NETWORK" \
  -p "${PORT}:5050" \
  -e FLASK_SECRET="ganti-dengan-secret-kuat" \
  -e PRESENSI_DB_PATH=/data/presensi.db \
  -v /mnt/ssd/hosting/presensi-app:/data \
  "$IMAGE"

echo "==> Done"
docker ps --filter "name=$CONTAINER"
