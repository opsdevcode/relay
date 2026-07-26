.PHONY: bootstrap up down logs ingest ingest-full install test test-local lint format typecheck security quality smoke verify ci build-k8s backstage-install backstage-dev backstage-test backstage-e2e up-backstage up-all down-backstage down-all

PA := apps/relay-assistant
BS := apps/backstage
COMPOSE := docker compose -f compose.yaml

bootstrap:
	@test -f .env || cp .env.example .env

install:
	pip install --no-cache-dir -e "./$(PA)[dev]"

up: bootstrap
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

up-backstage: bootstrap
	$(COMPOSE) --profile backstage up --build -d

# Alias: portal + Backstage (same as up-backstage).
up-all: up-backstage

down-backstage:
	$(COMPOSE) --profile backstage down

down-all: down-backstage

logs:
	$(COMPOSE) logs -f relay-assistant

ingest:
	$(COMPOSE) exec relay-assistant \
		python -m rag_ingestion.cli ingest

ingest-full:
	$(COMPOSE) exec relay-assistant \
		python -m rag_ingestion.cli ingest --full

catalog-discover:
	cd $(PA) && PYTHONPATH=src python3 -m catalog_discovery.cli sync

lint:
	cd $(PA) && ruff check src tests

format:
	cd $(PA) && ruff format src tests

typecheck:
	cd $(PA) && mypy src

security:
	cd $(PA) && bandit -r src -c pyproject.toml && pip-audit

quality: lint typecheck
	@cd $(PA) && ruff format --check src tests

# Unit tests on the host — no Docker (matches CI `test` job).
test-local:
	cd $(PA) && PYTHONPATH=src python3 -m pytest -q

test: test-local

# Unit tests inside the running relay-assistant container.
test-docker:
	$(COMPOSE) exec relay-assistant python -m pytest -q

smoke:
	@./scripts/smoke-local.sh

verify: test-docker smoke

# Full gate before PR (host tests + quality + security; stack optional for smoke).
ci: quality security test-local

backstage-install:
	cd $(BS) && yarn install --immutable

backstage-dev:
	cd $(BS) && yarn start

backstage-test:
	cd $(BS) && CI=true yarn test --passWithNoTests --watchAll=false

backstage-e2e:
	cd $(BS) && yarn test:e2e

build-k8s:
	docker build -t ghcr.io/opsdevcode/relay-assistant:local apps/relay-assistant
	docker build -t ghcr.io/opsdevcode/relay-web:local apps/web
