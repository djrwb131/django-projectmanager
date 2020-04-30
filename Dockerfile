FROM python:3.6-alpine3.11
ENV PYTHONUNBUFFERED 1
RUN apk add gcc musl-dev libffi-dev openssl-dev mariadb-connector-c-dev
RUN mkdir /code
WORKDIR /code
COPY Pipfile /code
RUN pip install pipenv
RUN pipenv install
COPY binaryblob_ca /code/
RUN apk del gcc musl-dev libffi-dev openssl-dev mariadb-connector-c-dev
RUN apk add mariadb-connector-c