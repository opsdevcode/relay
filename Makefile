.PHONY: bootstrap up down logs ingest test smoke build-k8s

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

smoke:
	@./scripts/smoke-local.sh

test:
	docker compose -f deploy/docker-compose.yml exec portal-assistant python -m pytest -q

build-k8s:
	docker build -t ghcr.io/opsdevcode/portal-assistant:local apps/portal-assistant
	docker build -t ghcr.io/opsdevcode/portal-web:local apps/web
