#!/usr/bin/env bash
set -euo pipefail

if [[ "${ELIO_RESTORE_CONFIRM:-}" != "RESTORE" ]]; then
  echo "Set ELIO_RESTORE_CONFIRM=RESTORE to allow restore execution."
  exit 1
fi

APP_DIR="${1:-${ELIO_SERVER_PATH:-$HOME/elio}}"
BACKUP_DIR="${2:-}"
PG_CLIENT_IMAGE="${ELIO_PG_CLIENT_IMAGE:-postgres:17}"

if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
  echo "Provide a valid backup directory."
  exit 1
fi

cd "$APP_DIR"

if [[ -f ".env" ]]; then
  ELIO_PG_URI="$(grep -E '^ELIO_PG_URI=' .env | head -n1 | cut -d= -f2- | tr -d '\r' || true)"
fi

if [[ -f "$BACKUP_DIR/database.dump" ]]; then
  docker run --rm \
    --network host \
    -e ELIO_PG_URI="$ELIO_PG_URI" \
    -v "$BACKUP_DIR:/backup" \
    "$PG_CLIENT_IMAGE" \
    sh -lc 'pg_restore --clean --if-exists --no-owner --dbname "$ELIO_PG_URI" /backup/database.dump'
fi

if [[ -f "$BACKUP_DIR/artifacts.tar.gz" ]]; then
  tar -xzf "$BACKUP_DIR/artifacts.tar.gz" -C "$APP_DIR"
fi

echo "Restore complete."
