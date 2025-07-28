
# ======================================================================================
# MISCELLANEOUS
# ======================================================================================

RED     := \033[0;31m
GREEN   := \033[0;32m
YELLOW  := \033[1;33m 
BLUE    := \033[0;34m
NC      := \033[0m

# ======================================================================================
# GENERAL CONFIGURATION
# ======================================================================================

SHELL := /bin/bash

COMPOSE_FILE ?= docker-compose.yml
COMPOSE_DEV_FILE ?= docker-compose.dev.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

# ======================================================================================
# DEFAULT TARGET & SELF-DOCUMENTATION
# ======================================================================================
.DEFAULT_GOAL := help

# Phony targets -don't represent files
.PHONY: app help up down logs ps build no-cache restart re config status clean fclean prune \
        stop start ssh exec inspect list-volumes list-networks rere rebuild it backend dev monitoring \
        format lint

# ======================================================================================
# HELP & USAGE
# ======================================================================================

help:
	@echo -e "$(BLUE)========================================================================="
	@echo -e " Lbro's Universal Docker Compose Makefile "
	@echo -e "=========================================================================$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Usage: make [target] [service=SERVICE_NAME] [args="ARGS"] [file=COMPOSE_FILE]$(NC)"
	@echo -e "  'service' specifies a single service for targets like logs, build, ssh, exec, inspect."
	@echo -e "  'args' specifies commands for 'exec'."
	@echo -e "  'file' specifies an alternative docker-compose file (default: docker-compose.yml)."
	@echo ""
	@echo -e "$(GREEN)Core Stack Management:$(NC)"
	@echo -e "  up                  - Start all services in detached mode (Alias: start)."
	@echo -e "  down                - Stop and remove all services and default network."
	@echo -e "  restart             - Restart all services (down + up)."
	@echo -e "  re                  - Rebuild images and restart all services (down + build + up)."
	@echo -e "  rere                - Rebuild images without cache and restart all services (down + no-cache + up)."
	@echo -e "  stop                - Stop all services without removing them."
	@echo ""
	@echo -e "$(GREEN)Service-Specific Management:$(NC)"
	@echo -e "  up-api              - Start API only."
	@echo -e "  up-frontend         - Start API and Frontend."
	@echo -e "  up-tui              - Start API and TUI (interactive)."
	@echo -e "  up-all              - Start all services (API, Frontend, TUI)."
	@echo -e "  frontend            - Start only frontend service."
	@echo -e "  frontend-dev        - Start frontend in development mode."
	@echo -e "  frontend-build      - Build frontend only."
	@echo -e "  frontend-logs       - Show frontend logs."
	@echo -e "  frontend-ssh        - SSH into frontend container."
	@echo ""
	@echo -e "$(GREEN)Building Images:$(NC)"
	@echo -e "  build [service=<name>] - Build images (all or specific service)."
	@echo -e "  no-cache [service=<name>] - Build images without cache (all or specific service)."
	@echo ""
	@echo -e "$(GREEN)Information & Debugging:$(NC)"
	@echo -e "  status [service=<name>] - Show status of services (all or specific) (Alias: ps)."
	@echo -e "  logs [service=<name>]   - Follow logs (all or specific service)."
	@echo -e "  config              - Validate and display effective Docker Compose configuration."
	@echo -e "  ssh service=<name>    - Get an interactive shell into a running service (Alias: it)."
	@echo -e "  exec service=<name> args=\"<cmd>\" - Execute a command in a running service."
	@echo -e "  inspect service=<name> - Inspect a running service container."
	@echo -e "  list-volumes        - List Docker volumes (may include non-project volumes)."
	@echo -e "  list-networks       - List Docker networks (may include non-project networks)."
	@echo ""
	@echo -e "$(GREEN)Cleaning & Pruning:$(NC)"
	@echo -e "  clean               - Remove stopped service containers and default network created by compose."
	@echo -e "  fclean              - Perform 'clean' and also remove volumes defined in compose file."
	@echo -e "  prune               - Prune unused Docker images, build cache, and dangling volumes (Docker system prune)."
	@echo ""
	@echo -e "$(YELLOW)Examples:$(NC)"
	@echo -e "  make up"
	@echo -e "  make logs service=my_backend"
	@echo -e "  make ssh service=my_app_container"
	@echo -e "  make build file=docker-compose.dev.yml"
	@echo -e "$(BLUE)========================================================================="
	@echo -e " Help Section End "
	@echo -e "=========================================================================$(NC)"

# ======================================================================================
# CORE STACK MANAGEMENT
# ======================================================================================

up: ## Start all services in detached mode
	@echo -e "$(GREEN)Igniting services from $(COMPOSE_FILE)... All systems GO!$(NC)"
	@$(COMPOSE) up -d --remove-orphans
	@echo -e "$(GREEN)Services are now running in detached mode.$(NC)"

start: ## Alias for up
	@echo -e "$(GREEN)Starting services from $(COMPOSE_FILE)... All systems GO!$(NC)"
	@$(COMPOSE) up -d --remove-orphans $(service)

down: ## Stop and remove all services and networks defined in the compose file
	@echo -e "$(RED)Shutting down services from $(COMPOSE_FILE)... Powering down.$(NC)"
	@$(COMPOSE) down --remove-orphans

stop: ## Stop all services without removing them
	@echo -e "$(YELLOW)Halting operations for $(COMPOSE_FILE)... Services stopping.$(NC)"
	@$(COMPOSE) stop $(service)

restart: down up ## Restart all services

re: down build up ## Rebuild images and restart all services

rere: down no-cache up ## Rebuild images without cache and restart all services

rebuild: down clean build up ## Alias for re

# ======================================================================================
# BUILDING IMAGES
# ======================================================================================

build: ## Build (or rebuild) images for specified service, or all if none specified
	@echo -e "$(BLUE)Forging components... Building images for $(or $(service),all services) from $(COMPOSE_FILE).$(NC)"
	@$(COMPOSE) build $(service)

no-cache: ## Build images without using cache for specified service, or all
	@echo -e "$(YELLOW)Force-forging (no cache)... Building for $(or $(service),all services) from $(COMPOSE_FILE).$(NC)"
	@$(COMPOSE) build --no-cache $(service)

# ======================================================================================
# INFORMATION & DEBUGGING
# ======================================================================================

status: ## Show status of running services
	@echo -e "$(BLUE)System Status Report for $(COMPOSE_FILE):$(NC)"
	@$(COMPOSE) ps $(service)

ps: status ## Alias for status

logs: ## Follow logs for specified service, or all if none specified
	@echo -e "$(BLUE)Tapping into data stream... Logs for $(or $(service),all services) from $(COMPOSE_FILE).$(NC)"
	@$(COMPOSE) logs -f --tail="100" $(service)

config: ## Validate and display effective Docker Compose configuration
	@echo -e "$(BLUE)Blueprint Configuration for $(COMPOSE_FILE):$(NC)"
	@$(COMPOSE) config

ssh: ## Get an interactive shell into a running service container
	@if [ -z "$(service)" ]; then \
		echo -e "$(RED)Error: Service name required. Usage: make ssh service=<service_name>$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)Establishing DirectConnect to $(service) from $(COMPOSE_FILE)... Standby.$(NC)"
	@$(COMPOSE) exec $(service) /bin/sh || $(COMPOSE) exec $(service) /bin/bash || echo -e "$(RED)Failed to find /bin/sh or /bin/bash in $(service).$(NC)"

it: ssh ## Alias for ssh

exec: ## Execute a command in a running service container
	@if [ -z "$(service)" ] || [ -z "$(args)" ]; then \
		echo -e "$(RED)Error: Service name and command required. Usage: make exec service=<service_name> args=\"<command>\"$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)Executing remote directive in $(service) (from $(COMPOSE_FILE)): $(args)...$(NC)"
	@$(COMPOSE) exec $(service) $(args)

inspect: ## Inspect a running service container
	@if [ -z "$(service)" ]; then \
		echo -e "$(RED)Error: Service name required. Usage: make inspect service=<service_name>$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)Performing deep scan of $(service) (from $(COMPOSE_FILE)) internals...$(NC)"
	@_container_id=$$(docker-compose -f $(COMPOSE_FILE) ps -q $(service) | head -n 1); \
	if [ -z "$$_container_id" ]; then \
		echo -e "$(RED)Service $(service) not found or not running.$(NC)"; \
		exit 1; \
	fi; \
	docker inspect $$_container_id

list-volumes: ## List Docker volumes
	@echo -e "$(BLUE)Global Docker Volumes (use 'docker volume ls --filter label=com.docker.compose.project=YOUR_PROJECT_NAME' for project specifics):$(NC)"
	@docker volume ls
	@echo -e "$(YELLOW)Note: For project-specific volumes, Docker Compose adds labels based on project name (usually dir name).$(NC)"

list-networks: ## List Docker networks
	@echo -e "$(BLUE)Global Docker Networks (use 'docker network ls --filter label=com.docker.compose.project=YOUR_PROJECT_NAME' for project specifics):$(NC)"
	@docker network ls

# ======================================================================================
# CLEANING & PRUNING
# ======================================================================================

clean: ## Remove stopped service containers and default network
	@echo -e "$(RED)Cleaning containers and networks from $(COMPOSE_FILE)...$(NC)"
	@$(COMPOSE) down --remove-orphans 

fclean: ## Remove containers, networks, volumes defined in compose file
	@echo -e "$(RED)Deep cleaning containers, networks, and volumes from $(COMPOSE_FILE)...$(NC)"
	@$(COMPOSE) down --volumes --remove-orphans --rmi 'all'

prune: fclean ## Prune all unused Docker resources
	@echo -e "$(RED)Pruning all unused Docker resources...$(NC)"
	@docker system prune -af --volumes
	@docker builder prune -af
	@docker volume prune -af 
	@echo -e "$(GREEN)Docker system prune complete.$(NC)"

# ======================================================================================
# APPLICATION SPECIFIC TARGETS
# ======================================================================================

backend: ## Start only backend service
	@$(COMPOSE) up -d --build backend && make logs 

frontend: ## Start only frontend service
	@$(COMPOSE) up -d --build gemini-frontend && make logs service=gemini-frontend

frontend-dev: ## Start frontend in development mode
	@echo -e "$(GREEN)Starting frontend in development mode...$(NC)"
	@cd frontend && npm run dev

frontend-build: ## Build frontend only
	@echo -e "$(BLUE)Building frontend...$(NC)"
	@$(COMPOSE) build gemini-frontend

frontend-logs: ## Show frontend logs
	@make logs service=gemini-frontend

frontend-ssh: ## SSH into frontend container
	@make ssh service=gemini-frontend

# ======================================================================================
# PROFILE TARGETS
# ======================================================================================

up-api: ## Start API only
	@$(COMPOSE) up -d gemini-api

up-frontend: ## Start API and Frontend
	@$(COMPOSE) up -d gemini-api gemini-frontend

up-tui: ## Start API and TUI
	@$(COMPOSE) --profile tui up -d

up-all: ## Start all services (API, Frontend, TUI)
	@$(COMPOSE) --profile tui up -d

# ======================================================================================
# NPM SCRIPTS
# ======================================================================================

format: ## Run code formatting
	@echo -e "$(YELLOW)Formatting code...$(NC)"
	@npm run format

lint: ## Run linter
	@echo -e "$(YELLOW)Linting code...$(NC)"
	@npm run lint

# ======================================================================================
# VARIABLE HANDLING
# ======================================================================================
ifeq ($(file),)
    # file is not set, use default COMPOSE_FILE
else
    COMPOSE_FILE := $(file)
    COMPOSE := docker compose -f $(COMPOSE_FILE)
endif

# Catch-all for targets that might not explicitly handle 'service' or 'args'
%:
	@:
