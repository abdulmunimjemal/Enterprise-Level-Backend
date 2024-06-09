APP_VERSION?=DEV-SNAPSHOT
APP_NAME?=mmbackend

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
	@poetry run pybe serve --host localhost --port 8000 --reload

run-app: build-app
	@echo "Running application"
	@poetry run pybe serve --host 0.0.0.0 --port 80

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

# Docker #######################################################################################

require-docker:
	@echo "Checking for Docker..."
	@command -v docker >/dev/null 2>&1 || (echo "Docker is required. Please install via 'make install-docker'." && exit 1)

test-app-docker: require-docker
	@echo "Testing application... (Containerised)"
	@$(call build_docker_image,development)
	@$(call run_docker_dev_mount,pytest -v)

check-format-docker: require-docker
	@echo "Checking application formatting... (Containerised)"
	@$(call build_docker_image,development)
	@$(call run_docker_dev_mount,black --check --line-length=120 .)

check-lint-docker: require-docker
	@echo "Checking application linting... (Containerised)"
	@$(call build_docker_image,development)
	@$(call run_docker_dev_mount,flake8 --show-source --statistics --count --max-line-length=120 .)

run-app-docker-dev: require-docker
	@docker stop fastapi-dev || true
	@echo "Running application in development mode... (Containerised)"
	@$(call build_docker_image,development)
	@$(call run_docker_dev_mount,,-d -p 8000:8000)

run-app-docker-prod: require-docker
	@echo "Running application in production mode... (Containerised)"
	@$(call build_docker_image,production)
	@docker run -p 80:80 --name fastapi-prod --rm $(IMAGE_ID)

export-production-image: require-docker
	@echo "Exporting Docker image..."
	@$(call build_docker_image,production)
	@mkdir -p $(IMAGE_SAVE_LOCATION)
	@docker save -o $(IMAGE_SAVE_LOCATION)/$(APP_NAME)-$(APP_VERSION).tar $(IMAGE_ID)

export-openapi-schema: run-app-docker-dev
	@echo "Exporting OpenAPI schema..."
	@mkdir -p $(OPENAPI_SAVE_LOCATION)
	@sleep 5
	@curl -s http://0.0.0.0:8000/openapi.json > $(OPENAPI_SAVE_LOCATION)/openapi.json
	@docker stop fastapi-dev || true
	@docker run --rm -v $(OPENAPI_SAVE_LOCATION):/build redocly/cli build-docs --api=/build/openapi.json --output=/build/index.html

# Functions ####################################################################################

define build_docker_image
	@echo "Building Docker image for target: $(1)"
	@docker build --target $(1) --build-arg APP_VERSION=$(APP_VERSION) --build-arg APP_NAME=$(APP_NAME) -t $(IMAGE_ID) .
endef

define run_docker_dev_mount
	@docker run $(2) \
		-v $(PWD)/src:/app/src \
		-v $(PWD)/tests:/app/tests \
		-v $(PWD)/.env:/app/.env \
		--rm --name fastapi-dev $(IMAGE_ID) $(1)
endef