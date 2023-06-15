# builder stage
FROM python:3.11-slim as builder

# install minimal dependencies for installing psycopg2 python module
RUN apt-get update && apt-get install -y libpq-dev gcc

# create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# install required python modules to virtual environment
COPY requirements.txt .
RUN python -m pip install --no-cache -r requirements.txt

# final stage
FROM python:3.11-slim

# don't buffer log messages
ENV PYTHONUNBUFFERED=1

# install libpg-dev dependency and remove apt package info to reduce image size
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

# create unprivileged ps2 user
RUN adduser --system --no-create-home --group ps2

# copy over virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# copy over application code
WORKDIR /code
COPY ./app /code/app

USER ps2

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
