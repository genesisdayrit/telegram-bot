.PHONY: install dev run lint test clean webhook-set webhook-info webhook-delete tunnel

# =============================================================================
# Setup
# =============================================================================

install:  ## Install production dependencies
	uv sync

dev:  ## Install all dependencies including dev
	uv sync --all-extras

# =============================================================================
# Development
# =============================================================================

run:  ## Run the development server
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:  ## Run linter
	uv run ruff check app/
	uv run ruff format --check app/

lint-fix:  ## Fix linting issues
	uv run ruff check --fix app/
	uv run ruff format app/

test:  ## Run tests
	uv run python -m pytest tests/ -v

# =============================================================================
# Webhook Management
# =============================================================================

webhook-set:  ## Register webhook with Telegram
	uv run python scripts/set_webhook.py set

webhook-info:  ## Get current webhook info
	uv run python scripts/set_webhook.py info

webhook-delete:  ## Delete webhook from Telegram
	uv run python scripts/set_webhook.py delete

# =============================================================================
# Local Development Helpers
# =============================================================================

tunnel:  ## Start ngrok tunnel (requires ngrok installed)
	ngrok http 8000

# =============================================================================
# Cleanup
# =============================================================================

clean:  ## Clean up cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache/ build/ dist/

# =============================================================================
# Help
# =============================================================================

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

