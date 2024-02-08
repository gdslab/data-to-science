# base image
FROM python:3.11-slim as python-base

# build args
ARG INSTALL_DEV=false
ARG NUM_OF_WORKERS=1

# do not buffer log messages and do not write byte code .pyc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# set dev mode
ENV DEV_MODE=$INSTALL_DEV

# set path to conda environment
ENV CONDA_ENV_PATH=/opt/conda/envs/d2s

# set number of workers for uvicorn process
ENV UVICORN_WORKERS=$NUM_OF_WORKERS

# matplotlib tmp dir
ENV MPLCONFIGDIR=/var/tmp/d2s

# image for building python environment
FROM condaforge/miniforge3:latest as conda-env-base

# env for conda environment file
ENV CONDA_ENV_DEPS=environment.yml

WORKDIR /opt

COPY $CONDA_ENV_DEPS ./

# allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN conda env create -f $CONDA_ENV_DEPS

FROM python-base as builder

# install dependencies
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl libpq-dev gcc bzip2 build-essential cmake ninja-build libpq-dev gdal-bin libgdal-dev wget && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

# fetch, build, and install pdal, entwine, and untwine
RUN wget https://github.com/PDAL/PDAL/releases/download/2.6.0/PDAL-2.6.0-src.tar.bz2 -O pdal.tar.bz2 \
    && wget https://github.com/connormanning/entwine/archive/refs/tags/3.0.0.tar.gz -O entwine.tar.gz \
    && wget https://github.com/hobuinc/untwine/archive/refs/tags/1.0.1.tar.gz -O untwine.tar.gz \
    && cd /tmp && tar -xf pdal.tar.bz2 && cd PDAL-2.6.0-src \
    && mkdir build && cd build && cmake -G Ninja .. && ninja && ninja install \
    && cd /tmp && tar -xf entwine.tar.gz && cd entwine-3.0.0 \
    && mkdir build && cd build && cmake -G Ninja .. && ninja && ninja install \
    && cd /tmp && tar -xf untwine.tar.gz && cd untwine-1.0.1 \
    && mkdir build && cd build && cmake .. && make && make install

# final stage
FROM python-base

WORKDIR /app/

# copy over virtual environment, pdal, entwine, and untwine from builder stage
COPY --from=conda-env-base $CONDA_ENV_PATH $CONDA_ENV_PATH
COPY --from=builder /usr/local/bin/pdal /usr/local/bin/pdal
COPY --from=builder /usr/local/lib/libpdalcpp.so.16 /usr/local/lib/libpdalcpp.so.16
COPY --from=builder /usr/local/bin/entwine /usr/local/bin/entwine
COPY --from=builder /usr/local/lib/libentwine.so.3 /usr/local/lib/libentwine.so.3
COPY --from=builder /usr/local/bin/untwine /usr/local/bin/untwine

# update path to include venv bin
ENV PATH="$CONDA_ENV_PATH/bin:$PATH"

# entwine and proj libs
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV PROJ_LIB="$CONDA_ENV_PATH/share/proj"

# install curl and gdal
RUN apt-get update && apt-get install -y curl gdal-bin && rm -rf /var/lib/apt/lists/*

# copy over application code
COPY . /app

# create user, create directory for logs, temp files, and user uploads, and update permissions
RUN useradd d2s \
    && mkdir -p /app/logs \
    && mkdir /var/tmp/d2s \
    && mkdir /static \
    && chown -R d2s:d2s /app \
    && chown -R d2s:d2s /static \
    && chown -R d2s:d2s /var/tmp/d2s \
    && chown -R d2s:d2s ${CONDA_ENV_PATH}

# change to non-root user
USER d2s

CMD /bin/bash /app/backend-start.sh
