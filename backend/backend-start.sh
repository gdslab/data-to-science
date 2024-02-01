#!/bin/bash

set -o errexit
set -o nounset

# check if database is ready
python /app/app/celeryworker_pre_start.py

# update database with any unapplied migrations
alembic upgrade head

# start uvicorn server
if [[ "$DEV_MODE" = true ]]; then
    uvicorn app.main:app --host 0.0.0.0 --port 5000  --reload
else
    uvicorn app.main:app --proxy-headers --workers ${UVICORN_WORKERS} --host 0.0.0.0 --port 5000
fi
