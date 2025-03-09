# base image
FROM python:3.11-slim AS python-base

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

# image for building python environment
FROM condaforge/miniforge3:latest AS conda-env-base

# do not write byte code .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# env for conda environment file
ENV CONDA_ENV_DEPS=environment.yml

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
RUN useradd d2s

# copy over virtual environment
COPY --from=conda-env-base --chown=d2s:d2s $CONDA_ENV_PATH $CONDA_ENV_PATH

# update path to include venv bin
ENV PATH="$CONDA_ENV_PATH/bin:$PATH"

# entwine and proj libs
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV PROJ_LIB="$CONDA_ENV_PATH/share/proj"

# install curl and gdal
RUN apt-get update && apt-get install -y curl gdal-bin rsync && rm -rf /var/lib/apt/lists/*

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
