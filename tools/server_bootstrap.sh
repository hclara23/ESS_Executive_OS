#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-${ELIO_SERVER_PATH:-$HOME/elio}}"
WITH_XTTS="${WITH_XTTS:-0}"
SHARED_HOST="${SHARED_HOST:-0}"
BOOTSTRAP_MODELS="${BOOTSTRAP_MODELS:-1}"
SEED_ADMIN="${SEED_ADMIN:-1}"
PREWARM_STACK="${PREWARM_STACK:-1}"
MODEL_LIST="${ELIO_BOOTSTRAP_MODELS:-qwen3:8b nomic-embed-text qwen2.5vl:7b}"

cd "$APP_DIR"

compose_args=(-f compose.yaml)
if [[ "$SHARED_HOST" == "1" ]]; then
  compose_args+=(-f compose.shared-host.yaml)
fi
if [[ "$WITH_XTTS" == "1" ]]; then
  compose_args+=(-f compose.xtts.yaml)
fi

docker compose "${compose_args[@]}" up -d --build

if [[ "$BOOTSTRAP_MODELS" == "1" ]]; then
  docker compose "${compose_args[@]}" up -d ollama
  for model in $MODEL_LIST; do
    docker compose "${compose_args[@]}" exec -T ollama ollama pull "$model"
  done
fi

docker compose "${compose_args[@]}" exec -T api env PYTHONPATH=/app python tools/postgres_setup.py --setup

if [[ "$SEED_ADMIN" == "1" && -n "${ELIO_ADMIN_USER:-}" && -n "${ELIO_ADMIN_PASS:-}" ]]; then
  docker compose "${compose_args[@]}" exec -T api env PYTHONPATH=/app python tools/seed_admin.py
fi

if [[ "$PREWARM_STACK" == "1" ]]; then
  docker compose "${compose_args[@]}" exec -T api env PYTHONPATH=/app python tools/prewarm_local_stack.py
fi

echo "Bootstrap complete."
