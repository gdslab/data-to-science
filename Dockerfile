FROM python:3.11-alpine as builder

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN python -m pip install --no-cache -r /code/requirements.txt

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
