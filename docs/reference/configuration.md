# Configuration

D2S uses environment files to configure its services. This document describes all available environment variables organized by file.

## `.env`

| Variable | Description |
|----------|-------------|
| `EXTERNAL_STORAGE` | Location where raw image zips and metadata will be sent for image processing jobs. It could be a mapped network drive or any other directory on the host machine. This **should be left empty** unless you have set up an image processing backend that works with the D2S image processing Celery task. |
| `TUSD_STORAGE` | Location of Docker managed volume or mapped host directory that stores user uploaded datasets. |
| `TILE_SIGNING_SECRET` | Secret key used for creating a signed URL that the client can use to access raster tiles and MVT tiles. |

## `frontend.env`

| Variable | Description |
|----------|-------------|
| `VITE_MAPBOX_ACCESS_TOKEN` | Mapbox access token for satellite imagery (optional). |
| `VITE_MAPTILER_API_KEY` | Maptiler API key for OSM labels (optional). |
| `VITE_TURNSTILE_SITE_KEY` | Cloudflare Turnstile site key for bot protection on registration (optional). Leave empty to disable. Must be paired with `TURNSTILE_SECRET_KEY` in `backend.env`. |

## `backend.env`

You must provide a value for `SECRET_KEY` in your `backend.env` file. Use a cryptographically secure random string of at least 32 characters.

| Variable | Description |
|----------|-------------|
| `API_PROJECT_NAME` | Name that will appear in the FastAPI docs. |
| `API_DOMAIN` | Domain used for accessing the application (e.g., `http://localhost` or `https://customdomain`). |
| `CELERY_BROKER_URL` | Address for local redis service. |
| `CELERY_RESULT_BACKEND` | Address for local redis service. |
| `ENABLE_BREEDBASE` | Enable/disable Breedbase connection endpoints (`true`/`false`). |
| `ENABLE_CAMPAIGNS` | Enable/disable campaign management endpoints (`true`/`false`). |
| `ENABLE_IFORESTER` | Enable/disable iForester integration endpoints (`true`/`false`). |
| `ENABLE_STAC` | Enable/disable STAC (SpatioTemporal Asset Catalog) endpoints (`true`/`false`). |
| `ENABLE_OPENTELEMETRY` | Enable/disable OpenTelemetry. Must also uncomment the `otel-collector` container and toggle the `backend` and `titiler` OpenTelemetry related environment settings in the docker compose config. Disabled by default. |
| `EXTENSIONS` | Can be used to enable extensions. Should be left blank typically. |
| `EXTERNAL_STORAGE` | Internal mount point for external storage. Should be blank unless you have a binding mount for external storage. |
| `EXTERNAL_VIEWER_URL` | Web application for displaying published STAC Items (optional). |
| `MAIL_ENABLED` | Enable SMTP email by changing value from `0` to `1`. |
| `MAIL_SERVER` | SMTP server address. |
| `MAIL_USERNAME` | Username for SMTP server. |
| `MAIL_PASSWORD` | Password for SMTP server. |
| `MAIL_FROM` | Sender email address. |
| `MAIL_FROM_NAME` | Name of sender. |
| `MAIL_ADMINS` | List of emails that should receive admin mail separated by commas. |
| `MAIL_PORT` | SMTP server port. |
| `MAPBOX_ACCESS_TOKEN` | Mapbox access token for satellite imagery (optional). |
| `POINT_LIMIT` | Total number of points to be used when generating point cloud preview images. |
| `RABBITMQ_HOST` | RabbitMQ hostname. Leave blank. |
| `RABBITMQ_USERNAME` | RabbitMQ username. Leave blank. |
| `RABBITMQ_PASSWORD` | RabbitMQ password. Leave blank. |
| `SECRET_KEY` | Secret key for signing and verifying JWT tokens. |
| `STAC_API_KEY` | Secret key that can be used for verification by STAC API. |
| `STAC_API_URL` | URL for a STAC API. |
| `STAC_API_TEST_URL` | URL for a STAC API that can be used for testing. |
| `STAC_BROWSER_URL` | URL for STAC Browser site connected to the STAC API. |
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile secret key for bot protection on registration (optional). Leave empty to disable. |
| `HTTP_COOKIE_SECURE` | Set to `1` to only send cookies over HTTPS, `0` to allow HTTP. |
| `LIMIT_MAX_REQUESTS` | Maximum number of requests a worker will handle before being restarted. |
| `UVICORN_WORKERS` | Number of uvicorn workers. |

## `db.env`

`POSTGRES_PASSWORD` should be assigned a secure password. The other environment variables can be left on the default values. `POSTGRES_HOST` should always be set to `db` unless the database service name is changed from `db` to another name in `docker-compose.yml`.

If you change `POSTGRES_USER` or `POSTGRES_HOST`, you must also update these environment variables with the new values under the `db` service in `docker-compose.yml`.

## `frontend/.env`

| Variable | Description |
|----------|-------------|
| `VITE_API_V1_STR` | Path for API endpoints. Do not change from default value unless the path has been changed in the backend. |
| `VITE_BRAND_FULL` | Full name of application. |
| `VITE_BRAND_SHORT` | Abbreviated name of application. |
| `VITE_BRAND_SLOGAN` | Slogan that appears on landing page. |
| `VITE_TITLE` | Page title. |
| `VITE_META_DESCRIPTION` | Description for search results and browser tabs. |
| `VITE_META_OG_TITLE` | Title for social media shares. |
| `VITE_META_OG_DESCRIPTION` | Description for social media shares. |
| `VITE_META_OG_TYPE` | Content type (e.g., `website`, `article`). |
| `VITE_SHOW_CONTACT_FORM` | Boolean (`0` or `1`) to indicate if Contact Form link should be shown (requires email service). |

## `frontend/.env.development`

| Variable | Description |
|----------|-------------|
| `VITE_META_OG_IMAGE` | Preview image URL for social media shares. |
| `VITE_META_OG_URL` | Hostname for site. |
