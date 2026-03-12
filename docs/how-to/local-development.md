# Local Development Setup

This guide covers building D2S from source with full environment configuration. It is intended for contributors and users who want to customize or extend the platform.

## Prerequisites

[Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) are required. Verify your setup:

```bash
docker --version
docker compose --version
```

## Copy environment files

Navigate to the root directory of the repository and copy the example environment files:

```bash
cp backend.example.env backend.env
cp db.example.env db.env
cp .env.example .env
cp frontend.example.env frontend.env
cp frontend/.env.example frontend/.env
cp frontend/example.env.development frontend/.env.development
```

For details on each variable, see the [Configuration](../reference/configuration.md) reference.

## Build Docker images

Copy the example Docker Compose file and build the images:

```bash
cp docker-compose.example.yml docker-compose.yml
docker compose build
```

## Start the containers

```bash
docker compose up -d
```

## Access the application

The D2S web application is available at `http://localhost:8000`. Replace `localhost` with the `DOMAIN` environment variable if you changed it. To use a different port, update the `ports` setting under the `proxy` service in `docker-compose.yml`.

## Access the API documentation

After starting the containers, interactive API documentation is available at:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Stop the containers

```bash
docker compose stop
```
