FROM python:3.11-slim as builder

WORKDIR /code

# install minimal dependencies for psycopg2 module
RUN apt-get update && apt-get install -y libpq-dev gcc

# install python environment
COPY ./requirements.txt /code/requirements.txt
RUN python -m pip install --no-cache -r /code/requirements.txt

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
