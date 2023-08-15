# base image
FROM python:3.11-slim as python-base

ENV POETRY_PATH=/opt/poetry \
    VENV_PATH=/opt/.venv \
    PATH="$POETRY_PATH/bin:$VENV_PATH/bin:$PATH"

# builder stage
FROM python-base as builder

# install minimal dependencies for installing psycopg2 python module
RUN apt-get update && apt-get install -y curl libpq-dev gcc

# install poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=$POETRY_PATH python && \
    cd /usr/local/bin && \
    ln -s $POETRY_PATH/bin/poetry && \
    poetry config virtualenvs.create false

# install poetry environment into fresh python venv
RUN python -m venv $VENV_PATH

WORKDIR /opt

COPY pyproject.toml poetry.lock .

# allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"

# final stage
FROM python-base

WORKDIR /app/

# do not buffer log messages and do not write byte code .pyc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# install libpg-dev dependency and remove apt package info to reduce image size
RUN apt-get update && apt-get install -y libpq-dev gdal-bin && rm -rf /var/lib/apt/lists/*

# create unprivileged ps2 user
# RUN adduser --system --no-create-home --group ps2
RUN useradd -u 1000 ps2

# copy over virtual environment from builder stage
COPY --from=builder $VENV_PATH $VENV_PATH

# update path to include venv bin
ENV PATH="$VENV_PATH/bin:$PATH"

# copy over application code
COPY . /app

# create directory for user uploads
RUN mkdir /user-data

# update permissions for ps2 user/group
RUN chown -R ps2:ps2 /app && chown -R ps2:ps2 /user-data

USER ps2

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "5000"]
