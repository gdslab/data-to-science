#!/bin/bash

# Generate a runtime configuration file with the environment variables
CONFIG_CONTENT="{\"mapboxAccessToken\": \"${VITE_MAPBOX_ACCESS_TOKEN}\", \"maptilerApiKey\": \"${VITE_MAPTILER_API_KEY}\", \"osmLabelFilter\": \"${VITE_OSM_LABEL_FILTER:-}\", \"turnstileSiteKey\": \"${VITE_TURNSTILE_SITE_KEY:-}\"}"

# Write to public folder (for development yarn server)
echo "$CONFIG_CONTENT" > /app/public/config.json

# Write to nginx html folder (for production) if it exists
if [ -d "/usr/share/nginx/html" ]; then
    echo "$CONFIG_CONTENT" > /usr/share/nginx/html/config.json
fi

exec "$@"