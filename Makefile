.PHONY: bootstrap up down logs ingest install test test-local lint format typecheck security quality smoke verify ci build-k8s

PA := apps/relay-assistant

bootstrap:
	@test -f .env || cp .env.example .env

install:
	pip install --no-cache-dir -e "./$(PA)[dev]"

up: bootstrap
	docker compose -f deploy/docker-compose.yml up --build -d

down:
	docker compose -f deploy/docker-compose.yml down

logs:
	docker compose -f deploy/docker-compose.yml logs -f relay-assistant

ingest:
	docker compose -f deploy/docker-compose.yml exec relay-assistant \
		python -m rag_ingestion.cli ingest

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
	docker compose -f deploy/docker-compose.yml exec relay-assistant python -m pytest -q

smoke:
	@./scripts/smoke-local.sh

verify: test-docker smoke

# Full gate before PR (host tests + quality + security; stack optional for smoke).
ci: quality security test-local

build-k8s:
	docker build -t ghcr.io/opsdevcode/relay-assistant:local apps/relay-assistant
	docker build -t ghcr.io/opsdevcode/relay-web:local apps/web
