#!/bin/sh
set -e

wait-for-it "$POSTGRES_HOST:$POSTGRES_PORT" -t 60

alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
