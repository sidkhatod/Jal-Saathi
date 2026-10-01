.PHONY: setup test lint

setup:
	@echo "Setting up Python packages..."
	cd cv && uv sync
	cd rl && uv sync
	cd backend && uv sync
	cd infra && uv sync
	cd data && uv sync
	@echo "Setting up Web frontend..."
	cd web && npm install

test:
	@echo "Running tests..."
	cd cv && uv run pytest
	cd rl && uv run pytest
	cd backend && uv run pytest
	cd infra && uv run pytest
	cd data && uv run pytest
	cd web && npm run test

lint:
	@echo "Running linter..."
	cd cv && uv run ruff check .
	cd rl && uv run ruff check .
	cd backend && uv run ruff check .
	cd infra && uv run ruff check .
	cd data && uv run ruff check .
	cd web && npm run lint
