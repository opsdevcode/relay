.PHONY: bootstrap up down logs ingest test test-local smoke verify ci build-k8s

bootstrap:
	@test -f .env || cp .env.example .env

up: bootstrap
	docker compose -f deploy/docker-compose.yml up --build -d

down:
	docker compose -f deploy/docker-compose.yml down

logs:
	docker compose -f deploy/docker-compose.yml logs -f portal-assistant

ingest:
	docker compose -f deploy/docker-compose.yml exec portal-assistant \
		python -m rag_ingestion.cli ingest

# Fast unit tests on the host — no Docker stack required (matches CI).
test-local:
	cd apps/portal-assistant && PYTHONPATH=src python3 -m pytest -q

# Unit tests inside the running portal-assistant container.
test:
	docker compose -f deploy/docker-compose.yml exec portal-assistant python -m pytest -q

# End-to-end HTTP checks against localhost:8080 — requires `make up`.
smoke:
	@./scripts/smoke-local.sh

# Full local gate before commit: unit tests in container + smoke (stack must be up).
verify:
	$(MAKE) test
	$(MAKE) smoke

# CI entrypoint — same as test-local.
ci: test-local

build-k8s:
	docker build -t ghcr.io/opsdevcode/portal-assistant:local apps/portal-assistant
	docker build -t ghcr.io/opsdevcode/portal-web:local apps/web
