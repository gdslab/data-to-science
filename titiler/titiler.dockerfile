FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

RUN python -m pip install --upgrade pip \
    && python -m pip install titiler.core gunicorn uvicorn

WORKDIR /app

COPY ./app .
COPY ./gunicorn_conf.py .

EXPOSE 8888

CMD ["gunicorn", "main:app", "-c", "/app/gunicorn_conf.py", "-k", "uvicorn.workers.UvicornWorker"]
