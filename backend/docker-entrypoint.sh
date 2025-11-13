#!/bin/sh
set -euo pipefail

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "[entrypoint] applying migrations"
  alembic -c backend/alembic.ini upgrade head
fi

exec "$@"
