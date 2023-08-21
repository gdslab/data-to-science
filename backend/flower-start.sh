#!/bin/bash

set -o errexit
set -o nounset

worker_ready() {
    celery -A app.worker inspect ping
}

until worker_ready; do
    echo 'Celery workers not available'
    sleep 1
done
echo 'Celery workers are available'

celery -A app.worker -b "${CELERY_BROKER_URL}" flower
