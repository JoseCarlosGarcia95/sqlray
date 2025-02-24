ARG PYTHON_VERSION=3.12.3-slim-bookworm

FROM python:${PYTHON_VERSION} AS base

WORKDIR /app

RUN apt-get update && apt-get install -y nano

COPY requirements.txt .
COPY setup.py .
COPY sqlray/ ./sqlray
COPY README.md .

RUN pip install --no-cache-dir .

ENTRYPOINT [ "sqlray" ]
