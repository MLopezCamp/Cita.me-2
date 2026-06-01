.PHONY: help deploy up down build logs ps clean restart status test \
        grafana redis-cmd rabbitmq-ui portainer-ui \
        start stop pull update prod-logs prod-ps prod-status

PROD = docker compose -f docker-compose.prod.yml

help:
	@echo ""
	@echo "  ┌─────────────────────────────────────────────────┐"
	@echo "  │  cita.me — Sistema de Citas Medicas             │"
	@echo "  └─────────────────────────────────────────────────┘"
	@echo ""
	@echo "  DESPLIEGUE RAPIDO (primera vez o maquina nueva):"
	@echo "    make deploy      — Un solo comando: configura, construye y levanta todo"
	@echo ""
	@echo "  Desarrollo (construye desde codigo local):"
	@echo "    make up          — Levantar TODO el stack"
	@echo "    make down        — Detener y eliminar contenedores"
	@echo "    make build       — Reconstruir imagenes y levantar"
	@echo "    make restart     — Reiniciar todo el stack"
	@echo "    make logs        — Ver logs de todos los servicios"
	@echo "    make ps          — Estado de contenedores"
	@echo "    make status      — Estado + URLs de acceso"
	@echo "    make test        — Test de salud de servicios"
	@echo "    make clean       — Limpieza nuclear (contenedores + volumenes)"
	@echo ""
	@echo "  Produccion (imagenes desde Docker Hub):"
	@echo "    make start       — Descargar imagenes y levantar el stack"
	@echo "    make stop        — Detener el stack de produccion"
	@echo "    make update      — Actualizar imagenes y reiniciar"
	@echo "    make prod-logs   — Ver logs del stack de produccion"
	@echo ""
	@echo "  Navegador:"
	@echo "    make grafana      — Abrir Grafana  (admin / citame2024)"
	@echo "    make redis-cmd    — Abrir Redis Commander"
	@echo "    make rabbitmq-ui  — Abrir RabbitMQ  (guest / guest)"
	@echo "    make portainer-ui — Abrir Portainer"
	@echo ""

deploy:
	@echo ""
	@echo "  cita.me — Despliegue limpio"
	@echo ""
	@test -f .env || (cp .env.example .env && echo "  [OK] .env creado desde .env.example")
	@test -f .env && echo "  [OK] .env encontrado"
	docker compose down -v --remove-orphans 2>/dev/null || true
	docker compose up -d --build
	@echo ""
	@echo "  Esperando que los servicios esten listos..."
	@sleep 8
	$(MAKE) test
	$(MAKE) status

up:
	docker compose up -d --build
	$(MAKE) status

down:
	docker compose down

build:
	docker compose down
	docker compose build --no-cache
	docker compose up -d
	$(MAKE) status

restart:
	docker compose restart

logs:
	docker compose logs -f

ps:
	docker compose ps

status:
	@echo ""
	@echo "cita.me — SERVICIOS ACTIVOS"
	@echo ""
	@echo "  API Backend:      http://localhost:8000"
	@echo "  Frontend:         http://localhost:3000"
	@echo "  Grafana:          http://localhost:3200"
	@echo "  Redis Commander:  http://localhost:8081"
	@echo "  RabbitMQ UI:      http://localhost:15672 (guest/guest)"
	@echo "  Portainer:        http://localhost:9000"
	@echo "  DB Viewer:        http://localhost:8080"
	@echo ""
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

test:
	@echo "Testeando servicios..."
	@curl -s http://localhost:8000/health | grep -q "healthy" && echo "  Backend OK" || echo "  Backend FAIL"
	@curl -s http://localhost:3200/api/health | grep -q "ok" && echo "  Grafana OK" || echo "  Grafana FAIL"
	@docker exec citame-redis redis-cli ping | grep -q "PONG" && echo "  Redis OK" || echo "  Redis FAIL"
	@docker exec citame-rabbitmq rabbitmq-diagnostics check_running > /dev/null 2>&1 && echo "  RabbitMQ OK" || echo "  RabbitMQ FAIL"

clean:
	docker compose down -v
	docker system prune -f

clean-all:
	docker compose down -v
	docker system prune -af --volumes

logs-backend:
	docker logs -f citame-backend

logs-worker:
	docker logs -f citame-worker

logs-redis:
	docker logs -f citame-redis

logs-rabbitmq:
	docker logs -f citame-rabbitmq

logs-grafana:
	docker logs -f citame-grafana

logs-alloy:
	docker logs -f citame-alloy

grafana:
	@start http://localhost:3200 || open http://localhost:3200 || xdg-open http://localhost:3200

redis-cmd:
	@start http://localhost:8081 || open http://localhost:8081 || xdg-open http://localhost:8081

rabbitmq-ui:
	@start http://localhost:15672 || open http://localhost:15672 || xdg-open http://localhost:15672

portainer-ui:
	@start http://localhost:9000 || open http://localhost:9000 || xdg-open http://localhost:9000

# ── Produccion (imagenes desde Docker Hub) ──────────────────────────────────

pull:
	$(PROD) pull

start:
	@test -f .env || (cp .env.example .env && echo "  [OK] .env creado desde .env.example")
	$(PROD) pull
	$(PROD) up -d
	@echo "  Esperando que los servicios esten listos..."
	@sleep 8
	$(MAKE) prod-status

stop:
	$(PROD) down

update:
	$(PROD) pull
	$(PROD) up -d

prod-logs:
	$(PROD) logs -f

prod-ps:
	$(PROD) ps

prod-status:
	@echo ""
	@echo "cita.me — SERVICIOS DE PRODUCCION ACTIVOS"
	@echo ""
	@echo "  Frontend:         http://localhost:3000"
	@echo "  API Backend:      http://localhost:8000"
	@echo "  Swagger:          http://localhost:8000/docs"
	@echo "  DB Viewer:        http://localhost:8080"
	@echo "  Redis Commander:  http://localhost:8081"
	@echo "  RabbitMQ UI:      http://localhost:15672 (guest/guest)"
	@echo "  Grafana:          http://localhost:3200"
	@echo "  Portainer:        http://localhost:9000"
	@echo ""
	@$(PROD) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"