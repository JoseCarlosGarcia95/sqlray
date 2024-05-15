ARG PYTHON_VERSION=3.12.3-slim-bookworm

FROM python:${PYTHON_VERSION} AS base

WORKDIR /app

COPY requirements.txt .
COPY setup.py .
COPY sqlray/ ./sqlray
COPY README.md .

RUN pip install --no-cache-dir .

ENTRYPOINT [ "sqlray" ]