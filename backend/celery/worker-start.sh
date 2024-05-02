#!/bin/bash

set -o errexit
set -o nounset

python /app/app/celeryworker_pre_start.py

celery -A app.tasks worker -l info -c 4
