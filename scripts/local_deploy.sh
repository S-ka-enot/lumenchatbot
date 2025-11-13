#!/usr/bin/env bash
# Simple local deploy helper for LumenPay chatbot
# Usage: ./scripts/local_deploy.sh [--no-build]

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR="${SCRIPT_DIR}/.."

NO_BUILD=0
if [[ ${1-} == "--no-build" ]]; then
  NO_BUILD=1
fi

echo "Working dir: ${ROOT_DIR}"
cd "${ROOT_DIR}"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found. Install Docker Desktop and try again." >&2
  exit 1
fi

echo "Stopping existing compose stack (if any)..."
docker compose down || true

if [[ "$NO_BUILD" -eq 0 ]]; then
  echo "Building images (this may take a few minutes)..."
  docker compose build --pull
fi

echo "Starting services in background..."
docker compose up -d

echo "Waiting 2s for containers to initialize..."
sleep 2

echo "Applying Alembic migrations (inside temporary container)..."
# Run migrations via a one-off container so that environment is same as service
docker compose run --rm backend alembic upgrade head || {
  echo "Migrations failed. See backend logs for details:" >&2
  docker compose logs backend --tail 200
  exit 1
}

echo "Migrations applied. Waiting for backend health endpoint..."

# Wait for health endpoint (max ~90s)
HEALTH_URL="http://localhost:8001/api/v1/health"
MAX_RETRIES=18
SLEEP_SEC=5
count=0
while true; do
  if curl -sS "$HEALTH_URL" >/dev/null 2>&1; then
    echo "Backend is healthy: ${HEALTH_URL}"
    break
  fi
  count=$((count+1))
  if [[ $count -ge $MAX_RETRIES ]]; then
    echo "Timeout waiting for backend health. Showing last backend logs:" >&2
    docker compose logs backend --tail 400
    exit 1
  fi
  echo "Waiting for backend health... ($count/$MAX_RETRIES)"
  sleep $SLEEP_SEC
done

echo "All done. Tail backend logs with: docker compose logs backend -f"

exit 0
