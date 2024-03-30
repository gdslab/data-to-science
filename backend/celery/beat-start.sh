#!/bin/bash

set -o errexit
set -o nounset

python /app/app/celeryworker_pre_start.py

celery -A app.tasks beat -s ${CELERY_BEAT_SCHEDULE} -l info
