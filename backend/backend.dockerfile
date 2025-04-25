# base image
FROM ubuntu:24.04 AS python-base

# build args
ARG INSTALL_DEV=false
ARG NUM_OF_WORKERS=1
ARG LIMIT_MAX_REQUESTS=10000

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

# limit max requests per process
ENV LIMIT_MAX_REQUESTS=$LIMIT_MAX_REQUESTS

# set path for celery beats schedule
ENV CELERY_BEAT_SCHEDULE=/var/run/celery/celerybeat-schedule

# matplotlib tmp dir
ENV MPLCONFIGDIR=/var/tmp/d2s

# Install Python and other system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-dev \
    curl \
    build-essential \
    cmake \
    rsync \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links for Python
RUN ln -s /usr/bin/python3.12 /usr/bin/python

# image for building python environment
FROM condaforge/miniforge3:latest AS conda-env-base

# do not write byte code .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# env for conda environment file
ENV CONDA_ENV_DEPS=environment.lock.yml

# install system dependencies
RUN apt-get update \
    && apt-get install -y curl build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

COPY $CONDA_ENV_DEPS ./

# allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN conda env create -f $CONDA_ENV_DEPS \
    && conda run -n d2s pip install staticmap redis types-python-jose types-passlib \
    && conda clean -afy \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete

# final stage
FROM python-base

WORKDIR /app/

# create d2s user
RUN userdel -r ubuntu 2>/dev/null || true \
    && groupadd -g 1000 d2s \
    && useradd -u 1000 -g 1000 d2s

# copy over virtual environment
COPY --from=conda-env-base --chown=d2s:d2s $CONDA_ENV_PATH $CONDA_ENV_PATH

# set environment variables
ENV GDAL_DATA="${CONDA_ENV_PATH}/share/gdal"
ENV LD_LIBRARY_PATH="${CONDA_ENV_PATH}/lib"
ENV PATH="${CONDA_ENV_PATH}/bin:${PATH}"
ENV PROJ_LIB="${CONDA_ENV_PATH}/share/proj"

# install untwine v1.5.0 from source
RUN mkdir -p /opt/untwine \
    && cd /opt/untwine \
    && curl -L https://github.com/hobuinc/untwine/releases/download/1.5.0/Untwine-1.5.0-src.tar.gz -o untwine-1.5.0.tar.gz \
    && tar -xzf untwine-1.5.0.tar.gz \
    && cd Untwine-1.5.0-src \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make \
    && make install \
    && cd /opt \
    && rm -rf /opt/untwine/untwine-1.5.0.tar.gz /opt/untwine/Untwine-1.5.0-src

# update LD_LIBRARY_PATH to include untwine library
ENV LD_LIBRARY_PATH="/opt/untwine/lib:${LD_LIBRARY_PATH}"

# copy over application code
COPY --chown=d2s:d2s . /app

# create directory for logs, temp files, and user uploads, and update permissions
RUN mkdir -p /app/logs \
    && mkdir /var/tmp/d2s \
    && mkdir /static \
    && mkdir /var/run/celery \
    && chown -R d2s:d2s /app/logs \
    && chown -R d2s:d2s /static \
    && chown -R d2s:d2s /var/run/celery \
    && chown -R d2s:d2s /var/tmp/d2s

# change to non-root user
USER d2s

CMD /bin/bash /app/backend-start.sh
