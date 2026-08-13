# Local Development Setup

This guide covers building D2S from source with full environment configuration. It is intended for contributors and users who want to customize or extend the platform.

## Prerequisites

[Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) are required. Verify your setup:

```bash
docker --version
docker compose --version
```

[uv](https://docs.astral.sh/uv/getting-started/installation/) is required only if you
change backend Python dependencies, which are locked with it. See
[Backend dependencies](#backend-dependencies).

```bash
uv --version
```

!!! note "Platform support"
    D2S containers target the `linux/x86_64` architecture. If you are running Docker Desktop on Apple Silicon (ARM), emulation is handled automatically, but you may notice slower build times and startup.

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

The backend image builds on top of `gdslab/d2s-geo-base`, a published image holding
GDAL, PDAL, PROJ, GEOS and Untwine compiled from source. Pull it first — its tag is
mutable, so an old local copy would be used silently:

```bash
docker pull gdslab/d2s-geo-base:latest
```

Building with `docker compose build --pull` folds that pull into the build, and
also refreshes the other base images the build uses. That is the form the
[deployment guide](deployment.md) uses; pulling the one image explicitly here
keeps the rest of your local base images as they are.

Copy the example Docker Compose file and build the images:

```bash
cp docker-compose.example.yml docker-compose.yml
docker compose build
```

If you need to build the base image yourself, for instance to change the GDAL
driver set, expect it to take 20-35 minutes:

```bash
docker build -f backend/geobase.dockerfile -t gdslab/d2s-geo-base:latest backend/
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

## Backend dependencies

Backend dependencies are declared in `backend/pyproject.toml` and locked in
`backend/uv.lock` by [uv](https://docs.astral.sh/uv/). To add or change one, edit
`pyproject.toml`, then regenerate the lock file and commit both:

```bash
cd backend
uv lock
```

Runtime dependencies go in `[project.dependencies]`. Test and lint tooling goes in
the `dev` dependency group, which is installed only when the image is built with
`INSTALL_DEV=true` — the development Compose files pass it, so production images
carry no test tooling.

Expect `uv lock` to change only the packages you touched. The resolver is pinned
to a fixed point in time by `exclude-newer` in `[tool.uv]`, so adding one dependency
resolves everything else to the versions already in the lock file rather than to
whatever is newest on PyPI today. Nothing published after that timestamp can enter
the tree, security releases included, until the timestamp moves. Bumping it is how
you deliberately take newer versions — do it as its own change, since it re-resolves
every package at once and the diff needs reading rather than skimming.

### Geospatial packages

`gdal`, `pdal`, `rasterio`, `fiona`, `pyogrio`, `shapely` and `pyproj` are pinned
exactly and compiled from source against the libraries in `gdslab/d2s-geo-base`,
rather than installed as prebuilt wheels. That keeps one copy of each native
library in the image and keeps the command line tools and the Python bindings on
the same GDAL.

Because of that coupling, changing the GDAL or PDAL version means rebuilding and
republishing the base image (`backend/geobase.dockerfile`, whose source versions
are pinned by checksum) and updating the matching `gdal==`/`pdal==` pins in
`pyproject.toml`, in the same pull request. The backend build compares the two and
fails if they disagree.

To check the whole stack in a running container:

```bash
docker compose exec backend bash /app/scripts/verify_geo_stack.sh
```

It asserts the GDAL drivers and PDAL stages the application uses, checks that the
Python bindings and the command line tools report the same versions, and exercises
paths the test suite does not cover, such as CSF pipelines and COG conversion.
