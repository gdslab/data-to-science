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

## Key configuration changes for production

- Set `HTTP_COOKIE_SECURE=1` in `backend.env` to enforce HTTPS-only cookies.
- Set `API_DOMAIN` to your production domain (e.g., `https://d2s.example.org`).
- Use a strong, unique value for `SECRET_KEY`.
- Configure SMTP settings (`MAIL_ENABLED=1`, `MAIL_SERVER`, etc.) for transactional email.
- Set `TILE_SIGNING_SECRET` to a secure random string.
- Adjust `UVICORN_WORKERS` and `LIMIT_MAX_REQUESTS` for your expected load.
