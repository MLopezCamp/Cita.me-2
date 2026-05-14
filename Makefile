.PHONY: up up-build start down restart logs \
        up-backend up-frontend up-infra \
        build-backend build-frontend \
        test-concurrencia test-concurrencia-v2 test-rabbitmq \
        ps clean

# ── Full stack ──────────────────────────────────────────────────────────────

up:
	docker-compose up

up-build:
	docker-compose up --build

start:
	docker-compose up --build

down:
	docker-compose down

restart:
	docker-compose down && docker-compose up --build

logs:
	docker-compose logs -f

ps:
	docker-compose ps

# ── Individual services ──────────────────────────────────────────────────────

up-infra:
	docker-compose up redis rabbitmq

up-backend:
	docker-compose up redis rabbitmq backend

up-frontend:
	docker-compose up frontend

# ── Local dev (without Docker) ───────────────────────────────────────────────

dev-backend:
	cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && pnpm dev

build-frontend:
	cd frontend && pnpm build

# ── Tests ────────────────────────────────────────────────────────────────────

test-concurrencia:
	cd backend && python test_concurrencia.py

test-concurrencia-v2:
	cd backend && python test_concurrencia_v2.py

test-rabbitmq:
	cd backend && python test_rabbitmq.py

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	docker-compose down -v --remove-orphans
