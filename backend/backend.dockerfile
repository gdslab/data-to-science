# Application image for the backend, celery worker, celery beat and flower.
#
# The native geospatial stack (GDAL, PDAL, PROJ, GEOS, Untwine) comes from
# gdslab/d2s-geo-base, built by geobase.dockerfile. The geospatial packages in
# pyproject.toml are compiled against it, so their pins and the versions that
# image was built from have to move together. The tag is mutable: pull it before
# building rather than trusting a local copy, or build it yourself if it has
# never been published here.

ARG GEO_BASE_IMAGE=gdslab/d2s-geo-base:latest
ARG UV_VERSION=0.12.3

FROM ${GEO_BASE_IMAGE} AS geo-base

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# Builds the Python environment. The geospatial packages have no usable wheels, or
# would vendor a second copy of GDAL, so they compile against /opt/geo here and the
# resulting virtualenv is copied into the final stage.
FROM ubuntu:24.04 AS python-builder

# The geo stack's own dependencies are needed here too: the sdists link against
# libgdal and friends, and pyproj's setup.py runs /opt/geo/bin/proj to read the
# PROJ version, which fails if those libraries cannot be resolved.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    build-essential \
    cmake \
    ninja-build \
    pkg-config \
    libpq-dev \
    curl \
    ca-certificates \
    libtiff6 \
    libjpeg-turbo8 \
    libpng16-16t64 \
    libopenjp2-7 \
    libdeflate0 \
    libzstd1 \
    liblzma5 \
    zlib1g \
    libsqlite3-0 \
    libexpat1 \
    libxml2 \
    libcurl4t64 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /usr/local/bin/
COPY --from=geo-base /opt/geo /opt/geo

# gdal-config, pdal-config, geos-config and pg_config are what the sdists read to
# find their libraries. The rpath means the extensions resolve /opt/geo without
# depending on LD_LIBRARY_PATH being set in whatever process loads them.
ENV PATH="/opt/geo/bin:${PATH}" \
    LD_LIBRARY_PATH=/opt/geo/lib \
    GDAL_CONFIG=/opt/geo/bin/gdal-config \
    PDAL_CONFIG=/opt/geo/bin/pdal-config \
    GEOS_CONFIG=/opt/geo/bin/geos-config \
    PROJ_DIR=/opt/geo \
    CMAKE_PREFIX_PATH=/opt/geo \
    LDFLAGS="-Wl,-rpath,/opt/geo/lib" \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=/usr/bin/python3.12 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

WORKDIR /build

COPY pyproject.toml uv.lock ./

# The gdal bindings are compiled against this image's libgdal and GDAL refuses to
# build them against an older one, so a stale geo-base already fails. This catches
# the other direction -- a geo-base rebuilt past the pin -- which would otherwise
# link bindings and library at different versions without complaint.
RUN . /opt/geo/VERSIONS \
    && pinned="$(sed -n 's/.*"gdal==\([0-9][^"]*\)".*/\1/p' pyproject.toml)" \
    && if [ "$pinned" != "$GDAL" ]; then \
        echo "geo base provides GDAL ${GDAL} but pyproject.toml pins gdal==${pinned}." >&2; \
        echo "Rebuild gdslab/d2s-geo-base or change the pin so the two agree." >&2; \
        exit 1; \
    fi

ARG INSTALL_DEV=false
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$INSTALL_DEV" = "true" ]; then \
        uv sync --frozen --no-install-project; \
    else \
        uv sync --frozen --no-install-project --no-dev; \
    fi \
    && uv pip check --python /opt/venv/bin/python \
    && find /opt/venv -name '*.so*' -type f \
        -exec sh -c 'strip --strip-unneeded "$1" 2>/dev/null || true' _ {} \; \
    && find /opt/venv -follow -type f -name '*.pyc' -delete

FROM ubuntu:24.04

ARG INSTALL_DEV=false
ARG NUM_OF_WORKERS=1
ARG LIMIT_MAX_REQUESTS=10000

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    ca-certificates \
    tzdata \
    curl \
    rsync \
    libtiff6 \
    libjpeg-turbo8 \
    libpng16-16t64 \
    libopenjp2-7 \
    libdeflate0 \
    libzstd1 \
    liblzma5 \
    zlib1g \
    libsqlite3-0 \
    libexpat1 \
    libxml2 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.12 /usr/bin/python

# ubuntu:24.04 ships a user at uid 1000, which d2s needs.
RUN userdel -r ubuntu 2>/dev/null || true \
    && groupadd -g 1000 d2s \
    && useradd -u 1000 -g 1000 d2s

# The stripped tree lands at /opt/geo so the rpaths and data paths baked into the
# libraries stay correct. Both stay root-owned: nothing at runtime writes to the
# interpreter, its packages or the native libraries.
COPY --from=geo-base /opt/geo-runtime /opt/geo
COPY --from=python-builder /opt/venv /opt/venv

# The virtualenv comes first on PATH so the start scripts and the AgTC endpoint,
# which all spawn a bare python/alembic/celery/uvicorn, get this interpreter.
ENV PATH="/opt/venv/bin:/opt/geo/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv \
    LD_LIBRARY_PATH=/opt/geo/lib \
    GDAL_DATA=/opt/geo/share/gdal \
    PROJ_LIB=/opt/geo/share/proj \
    PROJ_DATA=/opt/geo/share/proj \
    PDAL_DRIVER_PATH=/opt/geo/lib \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    DEV_MODE=$INSTALL_DEV \
    UVICORN_WORKERS=$NUM_OF_WORKERS \
    LIMIT_MAX_REQUESTS=$LIMIT_MAX_REQUESTS \
    CELERY_BEAT_SCHEDULE=/var/run/celery/celerybeat-schedule \
    MPLCONFIGDIR=/var/tmp/d2s

WORKDIR /app/

COPY --chown=d2s:d2s . /app

# directories for logs, temp files, and user uploads
RUN mkdir -p /app/logs \
    && mkdir /var/tmp/d2s \
    && mkdir /static \
    && mkdir /var/run/celery \
    && chown -R d2s:d2s /app/logs \
    && chown -R d2s:d2s /static \
    && chown -R d2s:d2s /var/run/celery \
    && chown -R d2s:d2s /var/tmp/d2s

USER d2s

CMD /bin/bash /app/backend-start.sh
