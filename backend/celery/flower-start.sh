#!/bin/bash

set -o errexit
set -o nounset

worker_ready() {
    celery -A app.core.celery_app inspect ping
}

until worker_ready; do
    echo 'Celery workers not available'
    sleep 1
done
echo 'Celery workers are available'

AUTH_ARG=""
if [ -n "${FLOWER_BASIC_AUTH:-}" ]; then
  AUTH_ARG="--basic_auth=${FLOWER_BASIC_AUTH}"
fi

celery -A app.core.celery_app -b "${CELERY_BROKER_URL}" flower --url_prefix=/celery ${AUTH_ARG}
