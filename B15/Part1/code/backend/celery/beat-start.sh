#!/bin/bash

set -o errexit
set -o nounset

python /app/app/celeryworker_pre_start.py

celery -A app.core.celery_app beat -s ${CELERY_BEAT_SCHEDULE} -l info
