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

# do not write byte code .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# env for conda environment file
ENV CONDA_ENV_DEPS=environment.yml

WORKDIR /opt

COPY $CONDA_ENV_DEPS ./

# allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN conda env create -f $CONDA_ENV_DEPS \
    && conda clean -afy \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete

# final stage
FROM python-base

WORKDIR /app/

# copy over virtual environment
COPY --from=conda-env-base $CONDA_ENV_PATH $CONDA_ENV_PATH

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
