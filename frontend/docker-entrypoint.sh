#!/bin/bash

# Generate a runtime configuration file with the environment variable
echo "{\"mapboxAccessToken\": \"${VITE_MAPBOX_ACCESS_TOKEN}\"}" >> /usr/share/nginx/html/config.json

exec "$@"