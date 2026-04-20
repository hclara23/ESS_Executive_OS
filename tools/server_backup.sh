#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-${ELIO_SERVER_PATH:-$HOME/elio}}"
BACKUP_ROOT="${2:-${ELIO_BACKUP_DIR:-$HOME/elio-backups}}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"
PG_CLIENT_IMAGE="${ELIO_PG_CLIENT_IMAGE:-postgres:17}"

mkdir -p "$BACKUP_DIR"
cd "$APP_DIR"

if [[ -f ".env" ]]; then
  ELIO_PG_URI="$(grep -E '^ELIO_PG_URI=' .env | head -n1 | cut -d= -f2- | tr -d '\r' || true)"
  ELIO_API_PORT="$(grep -E '^ELIO_API_PORT=' .env | head -n1 | cut -d= -f2- | tr -d '\r' || true)"
fi

docker compose ps > "$BACKUP_DIR/compose-ps.txt"
docker system df > "$BACKUP_DIR/docker-system-df.txt"

if [[ -n "${ELIO_PG_URI:-}" ]]; then
  docker run --rm \
    --network host \
    -e ELIO_PG_URI="$ELIO_PG_URI" \
    -v "$BACKUP_DIR:/backup" \
    "$PG_CLIENT_IMAGE" \
    sh -lc 'pg_dump "$ELIO_PG_URI" -Fc -f /backup/database.dump'
fi

if [[ -d "reports" || -d "voices/xtts" ]]; then
  tar -czf "$BACKUP_DIR/artifacts.tar.gz" \
    reports \
    voices/xtts \
    2>/dev/null || true
fi

docker compose exec -T api env PYTHONPATH=/app python tools/remote_runtime_snapshot.py --base-url "http://127.0.0.1:8000" > "$BACKUP_DIR/runtime.json" || true

echo "BACKUP_PATH=$BACKUP_DIR"
