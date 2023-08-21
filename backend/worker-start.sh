#!/bin/bash

set -o errexit
set -o nounset

python /app/app/celeryworker_pre_start.py

celery -A app.worker worker -l info -c 4 -Q main-queue
