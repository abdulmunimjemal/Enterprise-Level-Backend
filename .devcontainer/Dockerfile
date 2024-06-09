FROM mcr.microsoft.com/devcontainers/python:1-3.10-bullseye


ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PYTHONUNBUFFERED=1

RUN pip install poetry==1.4.2

WORKDIR /workspaces

RUN apt-get update \
  && apt-get -y install netcat gcc postgresql \
  && apt-get clean

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY pybe ./app

ENTRYPOINT ["python", "-m", "pybe.main:app"]
