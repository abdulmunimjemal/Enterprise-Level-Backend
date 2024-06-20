APP_VERSION?=0.0.1
APP_NAME?=moodme
PORT?=80
AWS_PROFILE?=moodme
ACCOUNT_NUMBER?=$(shell aws sts get-caller-identity --profile ${AWS_PROFILE} --query 'Account' --output text)

GIT_SHA_FETCH := $(shell git rev-parse HEAD | cut -c 1-8)

PUBLISH_REPO=$(APP_NAME)-repo
IMAGE_ID?=$(APP_NAME):$(APP_VERSION)
IMAGE_SAVE_LOCATION?=./build/images
OPENAPI_SAVE_LOCATION?=./build/openapi

# App ###################################
clean-app: require-poetry
	@echo "Cleaning application"
	@poetry run pyclean -v .

build-app: require-poetry
	@echo "Building application"
	@poetry install

test-app: install-dependencies
	@echo "Testing application"
	@poetry run pytest -v .

watch-test-app: install-dependencies
	@echo "Watching tests"
	@poetry run ptw

dev-app: build-app
	@echo "Running application"
	@poetry run pybe serve --host 0.0.0.0 --port 8000 --reload

run-app: build-app
	@echo "Running application"
	@poetry run pybe serve --host 0.0.0.0 --port ${PORT}

migration-new: install-dependencies
	@echo "Generating new migration"
	@poetry run alembic revision --autogenerate -m "${name}"

migration-up: install-dependencies
	@echo "Running migrations"
	@poetry run alembic upgrade head

migration-down: install-dependencies
	@echo "Rolling back migrations"
	@poetry run alembic downgrade head

# Dev ###################################
require-poetry:
	@echo "Checking for poetry"
	@command -v poetry >/dev/null 2>&1 || { echo "Poetry is not installed. Please install it and add it to your PATH."; exit 1; }

install-poetry:
	@echo "Installing poetry"
	@curl -sSf https://install.python-poetry.org | python -

install-dependencies: require-poetry
	@echo "Installing dependencies"
	@poetry install --compile --no-root

update-dependencies: require-poetry
	@echo "Updating dependencies"
	@poetry update

lock-dependencies: require-poetry
	@echo "Locking dependencies"
	@poetry lock

format-code: require-poetry
	@echo "Formatting code"
	@poetry run black .

lint-code: require-poetry
	@echo "Linting code"
	@poetry run ruff .

check-format: require-poetry
	@echo "Checking application formatting..."
	@poetry run black --check .

check-lint: require-poetry
	@echo "Checking application linting..."
	@poetry run flake8 --show-source --statistics --count .

make check-code-quality: check-format check-lint

# Docker ###################################
docker-build:
	@echo "Building docker image"
	@docker build -t ${IMAGE_ID} -f Dockerfile.prod .

docker-login:
	@echo "Logging in to docker"
	@aws ecr get-login-password --region us-east-1 --profile ${AWS_PROFILE} | docker login --username AWS --password-stdin ${ACCOUNT_NUMBER}.dkr.ecr.us-east-1.amazonaws.com

docker-push:
	@echo "Tagging docker image"
	@docker tag ${IMAGE_ID} ${PUBLISH_REPO}:${GIT_SHA_FETCH}
	@echo "Pushing docker image"
	@docker push ${PUBLISH_REPO}:${GIT_SHA_FETCH}

