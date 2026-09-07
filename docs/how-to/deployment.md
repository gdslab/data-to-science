# Deploy to Production

This guide covers deploying D2S to a production environment.

!!! warning "Work in progress"
    This guide is under development. For now, refer to the [Local Development Setup](local-development.md) guide as a starting point and adjust for your production environment.

## Overview

A production deployment of D2S involves:

1. Configuring environment variables with production-appropriate values (secure secrets, HTTPS domain, SMTP settings).
2. Building Docker images from the source or using prebuilt images.
3. Running the containers behind a reverse proxy with TLS.
4. Setting up persistent storage volumes for uploaded data.

When building from source, build with `docker compose build --pull`. The backend
image builds on `gdslab/d2s-geo-base:latest`, whose tag is mutable, so without
`--pull` a stale local copy of the geospatial stack is used silently. See
[Backend dependencies](local-development.md#backend-dependencies).

## Key configuration changes for production

- Set `HTTP_COOKIE_SECURE=1` in `backend.env` to enforce HTTPS-only cookies.
- Set `API_DOMAIN` to your production domain (e.g., `https://d2s.example.org`).
- Use a strong, unique value for `SECRET_KEY`.
- Configure SMTP settings (`MAIL_ENABLED=1`, `MAIL_SERVER`, etc.) for transactional email.
- Set `TILE_SIGNING_SECRET_KEY` to a secure random string.
- Adjust `UVICORN_WORKERS` and `LIMIT_MAX_REQUESTS` for your expected load.

## Sizing TiTiler

TiTiler reads COGs straight from the shared `user-data` volume, so the HTTP
range-request tuning in TiTiler's own documentation does not apply. The image
honors only `HOST`, `PORT`, and `WEB_CONCURRENCY`; every other gunicorn option
is passed through `GUNICORN_CMD_ARGS`.

- Run one worker per CPU given to the container and set the `cpus` limit to
  match. The example ships two workers on two CPUs.
- `GDAL_CACHEMAX` is megabytes per worker process. Budget the container memory
  limit at roughly `workers x (GDAL_CACHEMAX + 1 GB)`; the example's 4 GB limit
  covers two workers at 512 MB.
- Tile requests are not logged by default. Add `--access-logfile -` to
  `GUNICORN_CMD_ARGS` to log each one, or set `TITILER_API_DEBUG=True` for
  per-request logging with query parameters and a `Server-Timing` header.

## Upgrading

`docker-compose.prod.yml` is not tracked in git, so image tags in your deployment
copy do not change when you pull a release. Compare it against
`docker-compose.prod.example.yml` after each upgrade.

D2S requires **TiTiler 2.0 or later**. Set the `titiler` image tag to `2.2.1` in
your `docker-compose.prod.yml`:

```yaml
  titiler:
    image: ghcr.io/developmentseed/titiler:2.2.1
```

Raster tiles fail with HTTP 422 on TiTiler 1.x, because the tile URL format
changed in TiTiler 2.0. The backend logs the detected version on startup and
reports it at `/api/v1/health`, so check there if tiles stop rendering after an
upgrade. Roll out the backend, frontend, and titiler containers together.

Expect a brief load increase on TiTiler right after the upgrade: the tile URLs
changed, so Varnish starts with a cold cache and regenerates tiles on demand.
