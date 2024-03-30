#!/bin/bash

set -o errexit
set -o nounset

worker_ready() {
    celery -A app.tasks inspect ping
}

until worker_ready; do
    echo 'Celery workers not available'
    sleep 1
done
echo 'Celery workers are available'

celery -A app.tasks -b "${CELERY_BROKER_URL}" flower
