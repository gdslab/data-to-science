# Local Development Guide

This guide covers building D2S from source with full environment configuration. It is intended for contributors and users who want to customize or extend the platform.

## Prerequisites

[Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) are required to run the container with the following instructions. If you can successfully run `docker --version` and `docker compose --version` from a terminal then you are ready to proceed to the next section.

## Copy env example files

1. Navigate to the root directory of the repository.
2. Copy `backend.example.env` to a new file named `backend.env`.
   ```
   cp backend.example.env backend.env
   ```
3. Copy `db.example.env` to a new file named `db.env`.
   ```
   cp db.example.env db.env
   ```
4. Copy `.env.example` to a new file named `.env`.
   ```
   cp .env.example .env
   ```
5. Copy `frontend.example.env` to a new file named `frontend.env`.
   ```
   cp frontend.example.env frontend.env
   ```
6. Copy `frontend/.env.example` to a new file named `frontend/.env`.
   ```
   cp frontend/.env.example frontend/.env
   ```
7. Copy `frontend/example.env.development` to a new file named `frontend/.env.development`.
   ```
   cp frontend/example.env.development frontend/.env.development
   ```

## Configuration Options

D2S can be customized through environment variables defined in several `.env` files. The example files copied in the previous step contain sensible defaults, but you can adjust settings for branding, email, authentication, external services, and more.

For a complete reference of all available environment variables, see the [Configuration Options](options.md) documentation.

## Build Docker images for services

1. In the root repository directory where `docker-compose.example.yml` is located. Copy it to a new file named `docker-compose.yml`.

   ```
   cp docker-compose.example.yml docker-compose.yml
   ```

2. Build Docker images for the frontend, backend, and proxy services with the following command:
   ```
   docker compose build
   ```

## Start the containers

1. Use the following command to run the service containers in the background:
   ```
   docker compose up -d
   ```

## Stop the containers

1. Use the following command to stop the containers:
   ```
   docker compose stop
   ```

## Accessing the web application

The Data To Science web application can be accessed from `http://localhost:8000`. Replace `localhost` with the `DOMAIN` environment variable if it was changed to a different value. If port `8000` is already use, or you want to use a different port, change the port in `docker-compose.yml` under the `proxy` service's `ports` setting.

## Accessing the API

After running `docker compose up -d`, you should be able to access the web API from [http://localhost:8000/docs](http://localhost:8000/docs) or [http://localhost:8000/redoc](http://localhost:8000/redoc). The first URL will display the Swagger UI documentation for the API and the second URL will display the ReDoc documentation. The API endpoints can be tried out from either URL.

## Running backend tests

The `pytest` library can be used to run tests for the FastAPI backend. Use the following command to run the full test suite:

```
docker compose exec backend pytest
```

## Database migrations with Alembic

If you make any changes the database models, run the following command to create a new migration:

```
docker compose exec backend alembic revision --autogenerate -m "migration comment"
```

After creating the new migration, use the following command to update to the tables in the database:

```
docker compose exec backend alembic upgrade head
```

## Generating Vector Format Files (GeoParquet & FlatGeobuf)

Vector layers are automatically exported to GeoParquet and FlatGeobuf formats for efficient access from QGIS and other desktop GIS tools. For existing vector layers created before these features were added, use the backfill command to generate format files:

```bash
# Generate all formats (GeoParquet and FlatGeobuf) for all vector layers
docker compose exec backend python app/utils/generate_vector_formats.py

# Generate only GeoParquet for all layers
docker compose exec backend python app/utils/generate_vector_formats.py --format parquet

# Generate only FlatGeobuf for all layers
docker compose exec backend python app/utils/generate_vector_formats.py --format flatgeobuf

# Generate for a specific project
docker compose exec backend python app/utils/generate_vector_formats.py --project-id <project-uuid>

# Force regeneration of existing files
docker compose exec backend python app/utils/generate_vector_formats.py --force
```

The command will display progress per format and provide a summary of generated, skipped, and failed files for each format.
