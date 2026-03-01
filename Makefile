.PHONY: help install build up down stop start restart clean logs ps test mcp migrate migrate-status db-backup db-restore update

COMPOSE := docker compose
BACKEND := backend
FRONTEND := frontend
MCP_SERVER := mcp-server

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install frontend dependencies (run once before first build)
	cd frontend && npm install

build: ## Build all Docker images
	$(COMPOSE) build frontend backend
	$(COMPOSE) build mcp-server

up: ## Start backend and frontend services (detached)
	$(COMPOSE) up -d

down: ## Stop and remove containers, networks (keeps volumes)
	$(COMPOSE) down

stop: ## Stop running containers without removing them
	$(COMPOSE) stop

logs: ## Follow logs from all services (Ctrl+C to exit)
	$(COMPOSE) logs -f

logs-backend: ## Follow backend logs
	$(COMPOSE) logs -f $(BACKEND)

logs-frontend: ## Follow frontend logs
	$(COMPOSE) logs -f $(FRONTEND)

ps: ## Show container status
	$(COMPOSE) ps

clean: ## Remove containers, networks, and volumes (full reset)
	@echo "WARNING: This will remove all containers, networks, and volumes (including your database)."
	@read -p "Type 'yes' to confirm: " CONFIRM; \
	if [ "$$(echo $$CONFIRM | tr '[:upper:]' '[:lower:]')" = "yes" ]; then \
		$(COMPOSE) down -v; \
	else \
		echo "Aborted."; \
		exit 1; \
	fi

shell-backend: ## Open shell in backend container
	$(COMPOSE) exec $(BACKEND) /bin/bash

shell-frontend: ## Open shell in frontend container
	$(COMPOSE) exec $(FRONTEND) /bin/sh

shell-database: ## Open psql shell in postgres container
	$(COMPOSE) exec postgres psql -U oliver -d oliver

BACKUP_DIR := backups

db-backup: ## Create a database backup (optional: FILE=name)
	@mkdir -p $(BACKUP_DIR)
	@if [ -n "$(FILE)" ]; then \
		BACKUP_FILE="$(BACKUP_DIR)/$(FILE).sql"; \
	else \
		BACKUP_FILE="$(BACKUP_DIR)/oliver_$$(date +%Y%m%d_%H%M%S).sql"; \
	fi; \
	echo "Creating backup: $$BACKUP_FILE"; \
	$(COMPOSE) exec -T postgres pg_dump -U oliver oliver > "$$BACKUP_FILE"; \
	echo "Backup complete: $$BACKUP_FILE"

db-restore: ## Restore database from backup file (usage: make db-restore FILE=backups/filename.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter required. Usage: make db-restore FILE=backups/filename.sql"; \
		exit 1; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: File not found: $(FILE)"; \
		exit 1; \
	fi
	@echo "WARNING: This will overwrite the current database."
	@read -p "Type 'yes' to confirm: " CONFIRM; \
	if [ "$$(echo $$CONFIRM | tr '[:upper:]' '[:lower:]')" = "yes" ]; then \
		echo "Restoring from: $(FILE)"; \
		$(COMPOSE) exec -T postgres psql -U oliver -d oliver < "$(FILE)"; \
		echo "Restore complete."; \
	else \
		echo "Aborted."; \
		exit 1; \
	fi

migrate: ## Run Alembic migrations (alembic upgrade head)
	$(COMPOSE) exec $(BACKEND) alembic upgrade head

migrate-status: ## Show current Alembic migration status
	$(COMPOSE) exec $(BACKEND) alembic current

reset: db-backup down clean build up ## Full reset: clean, rebuild, start fresh

start:
	$(MAKE) build
	$(COMPOSE) down $(BACKEND) $(FRONTEND)
	$(COMPOSE) up -d $(BACKEND) $(FRONTEND)

restart: ## Restart backend and frontend services (with database backup)
	$(MAKE) db-backup
	$(MAKE) build
	$(COMPOSE) down $(BACKEND) $(FRONTEND)
	$(COMPOSE) up -d $(BACKEND) $(FRONTEND)

update: ## Pull latest code, backup DB, migrate, rebuild frontend/backend
	git pull
	$(MAKE) restart

install-mcp: install-mcp-claude-code install-mcp-claude-desktop ## Install Oliver MCP server for Claude Code and Claude Desktop

uninstall-mcp: uninstall-mcp-claude-code uninstall-mcp-claude-desktop ## Uninstall Oliver MCP server from Claude Code and Claude Desktop

uninstall-mcp-claude-code: ## Uninstall Oliver MCP server from Claude Code
	claude mcp remove oliver

uninstall-mcp-claude-desktop: ## Uninstall Oliver MCP server from Claude Desktop
	@python3 -c "\
import json, os, sys; \
p = sys.platform; \
cfg = os.path.expanduser('~/Library/Application Support/Claude/claude_desktop_config.json') if p == 'darwin' \
    else os.path.join(os.environ.get('APPDATA',''), 'Claude', 'claude_desktop_config.json'); \
os.path.exists(cfg) or (print('Config not found:', cfg) or sys.exit(0)); \
data = json.load(open(cfg)); \
removed = data.get('mcpServers', {}).pop('oliver', None); \
json.dump(data, open(cfg, 'w'), indent=2); \
print('Removed Oliver MCP from Claude Desktop:', cfg) if removed else print('Oliver MCP not found in Claude Desktop config') \
"

install-mcp-claude-code: ## Install Oliver MCP server for Claude Code
	claude mcp add oliver -- docker compose -f $(CURDIR)/docker-compose.yml run --rm -i -T mcp-server

install-mcp-claude-desktop: ## Install Oliver MCP server for Claude Desktop
	@OLIVER_PATH="$(CURDIR)" python3 -c "\
import json, os, sys; \
p = sys.platform; \
cfg = os.path.expanduser('~/Library/Application Support/Claude/claude_desktop_config.json') if p == 'darwin' \
    else os.path.join(os.environ.get('APPDATA',''), 'Claude', 'claude_desktop_config.json'); \
os.makedirs(os.path.dirname(cfg), exist_ok=True); \
data = json.load(open(cfg)) if os.path.exists(cfg) else {}; \
data.setdefault('mcpServers', {})['oliver'] = {'command': 'docker', 'args': ['compose', '-f', os.environ['OLIVER_PATH'] + '/docker-compose.yml', 'run', '--rm', '-i', '-T', 'mcp-server']}; \
json.dump(data, open(cfg, 'w'), indent=2); \
print('Installed Oliver MCP for Claude Desktop:', cfg) \
"
