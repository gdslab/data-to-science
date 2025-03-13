#!/bin/bash

set -o errexit
set -o nounset

python /app/app/celeryworker_pre_start.py

# Default to 4 workers if not set
CELERY_CONCURRENCY=${CELERY_WORKERS:-4}

celery -A app.core.celery_app worker -l info -c "${CELERY_CONCURRENCY}"
