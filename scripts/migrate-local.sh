#!/usr/bin/env bash
set -euo pipefail

echo "[local-migrate] Bringing up containers (no mock override)"
docker compose -f docker-compose.yml up -d --build

echo "[local-migrate] Waiting for API"
for i in $(seq 1 20); do
  if docker compose -f docker-compose.yml exec -T api python -c 'print(1)' >/dev/null 2>&1; then
    break
  fi
  echo "  waiting... ($i)"; sleep 2
done

echo "[local-migrate] Running Alembic upgrade on RDS"
# PYTHONPATH is cleared to avoid shadowing site-packages alembic by /app/alembic package name
docker compose -f docker-compose.yml exec -T api bash -lc 'PYTHONPATH= alembic upgrade head && PYTHONPATH= alembic current'

echo "[local-migrate] Done"

