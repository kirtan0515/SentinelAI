# ============================================================================
# SentinelAI - Enterprise AI Security Gateway
# Makefile for common development and deployment tasks
#
# Usage:
#   make help       - Show all available targets
#   make up         - Start all services
#   make test       - Run backend tests
#   make lint       - Lint backend code
# ============================================================================

.PHONY: up down build logs test test-security lint format migrate migration seed \
        frontend-dev frontend-build clean help

# Default target
.DEFAULT_GOAL := help

# ========================
# Docker Compose
# ========================

up: ## Start all services in detached mode
	docker-compose up -d

down: ## Stop all services
	docker-compose down

build: ## Build all Docker images
	docker-compose build

logs: ## Follow logs from all services
	docker-compose logs -f

# ========================
# Backend Testing
# ========================

test: ## Run backend pytest suite
	cd backend && python -m pytest -v --tb=short

test-security: ## Run security tests only
	cd backend && python -m pytest -v --tb=short -m security

# ========================
# Code Quality
# ========================

lint: ## Run ruff linter on backend
	cd backend && ruff check .

format: ## Run ruff formatter on backend
	cd backend && ruff format .

# ========================
# Database
# ========================

migrate: ## Run alembic migrations (upgrade to head)
	cd backend && alembic upgrade head

migration: ## Create new alembic migration (usage: make migration msg="add users table")
	cd backend && alembic revision --autogenerate -m "$(msg)"

seed: ## Seed the database with initial data
	cd backend && python scripts/seed-db.py

# ========================
# Frontend
# ========================

frontend-dev: ## Start frontend dev server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

# ========================
# Cleanup
# ========================

clean: ## Remove generated files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/node_modules
	rm -rf frontend/.next

# ========================
# Help
# ========================

help: ## Show this help message
	@echo "SentinelAI - Available Make Targets"
	@echo "===================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
