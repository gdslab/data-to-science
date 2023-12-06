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

# install libpg-dev, pdal, and entwine dependencies and remove apt package info to reduce image size
RUN apt-get update && apt-get install -y bzip2 build-essential cmake ninja-build libpq-dev gdal-bin libgdal-dev wget && rm -rf /var/lib/apt/lists/*

# install entwine and its dependencies
RUN mkdir /app/tools && cd /app/tools \
  && wget https://github.com/PDAL/PDAL/releases/download/2.6.0/PDAL-2.6.0-src.tar.bz2 \
  && wget https://github.com/connormanning/entwine/archive/refs/tags/3.0.0.tar.gz

RUN cd /app/tools && tar -xf PDAL-2.6.0-src.tar.bz2 && cd PDAL-2.6.0-src \
  && mkdir build && cd build && cmake -G Ninja .. && ninja && ninja install

RUN cd /app/tools && tar -xf 3.0.0.tar.gz && cd entwine-3.0.0 \
  && mkdir build && cd build && cmake -G Ninja .. && ninja && ninja install

# create unprivileged d2s user
RUN useradd d2s

# copy over virtual environment from builder stage
COPY --from=builder $VENV_PATH $VENV_PATH

# update path to include venv bin
ENV PATH="$VENV_PATH/bin:$PATH"
# entwine lib
ENV LD_LIBRARY_PATH=/usr/local/lib

# copy over application code
COPY . /app

# create directory for user uploads
RUN cd /app && mkdir /static

# update permissions for d2s user/group
RUN chown -R d2s:d2s /app && chown -R d2s:d2s /static

USER d2s

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "5000"]
