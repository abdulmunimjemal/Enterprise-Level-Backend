FROM python:3.11-buster as builder

RUN pip install poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN python -m venv /app/.venv \
    && . /app/.venv/bin/activate \
    && poetry install --only main --without dev --no-root \
    && rm -rf $POETRY_CACHE_DIR

WORKDIR /app

FROM python:3.11-slim-buster as certmaster

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY pyproject.toml poetry.lock ./
COPY . .
RUN pip install poetry && poetry install && poetry run pybe generate-privkey


# The runtime image, used to just run the code provided its virtual environment
FROM python:3.11-slim-buster as runtime

RUN apt-get update -yq && apt-get install -yq libpq-dev make

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=certmaster /app/certs ./certs

COPY .env .
COPY . .
COPY alembic.ini ./app/alembic.ini

# RUN ${VIRTUAL_ENV}/bin/poetry run pybe generate-privkey

CMD ["poetry", "run", "pybe", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
