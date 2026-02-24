.PHONY: help install build up down stop start restart clean logs ps test mcp migrate migrate-status

COMPOSE := docker compose
BACKEND := backend
FRONTEND := frontend

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install frontend dependencies (run once before first build)
	cd frontend && npm install

build: ## Build all Docker images
	$(COMPOSE) build

up: ## Start backend and frontend services (detached)
	$(COMPOSE) up -d

down: ## Stop and remove containers, networks (keeps volumes)
	$(COMPOSE) down

stop: ## Stop running containers without removing them
	$(COMPOSE) stop

start: ## Start stopped containers
	$(COMPOSE) start

logs: ## Follow logs from all services (Ctrl+C to exit)
	$(COMPOSE) logs -f

logs-backend: ## Follow backend logs
	$(COMPOSE) logs -f $(BACKEND)

logs-frontend: ## Follow frontend logs
	$(COMPOSE) logs -f $(FRONTEND)

ps: ## Show container status
	$(COMPOSE) ps

mcp-build: ## Build MCP server image only
	$(COMPOSE) build mcp-server

clean: ## Remove containers, networks, and volumes (full reset)
	@echo "WARNING: This will remove all containers, networks, and volumes (including your database)."
	@read -p "Type 'yes' to confirm: " CONFIRM; \
	if [ "$$(echo $$CONFIRM | tr '[:upper:]' '[:lower:]')" = "yes" ]; then \
		$(COMPOSE) down -v; \
	else \
		echo "Aborted."; \
		exit 1; \
	fi

dev: ## Start in development mode with live logs
	$(COMPOSE) up --build

dev-backend: ## Start only backend with logs
	$(COMPOSE) up --build $(BACKEND)

dev-frontend: ## Start only frontend with logs
	$(COMPOSE) up --build $(FRONTEND)

shell-backend: ## Open shell in backend container
	$(COMPOSE) exec $(BACKEND) /bin/bash

shell-frontend: ## Open shell in frontend container
	$(COMPOSE) exec $(FRONTEND) /bin/sh

db-shell: ## Open SQLite shell in backend container
	$(COMPOSE) exec $(BACKEND) sqlite3 /data/oliver.db

migrate: ## Run Alembic migrations (alembic upgrade head)
	$(COMPOSE) exec $(BACKEND) alembic upgrade head

migrate-status: ## Show current Alembic migration status
	$(COMPOSE) exec $(BACKEND) alembic current

reset: down clean build build-mcp up ## Full reset: clean, rebuild, start fresh

restart: down build build-mcp up
