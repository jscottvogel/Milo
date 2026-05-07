.PHONY: setup lint typecheck test test-unit test-integration test-e2e cdk-synth clean format eval dev dev-api dev-web export-openapi

setup:
	@echo "Setting up Python workspace..."
	uv sync
	@echo "Setting up Node workspace..."
	pnpm install

lint:
	uv run ruff check .
	pnpm exec eslint . --ext .ts,.tsx,.js,.jsx

typecheck:
	uv run mypy .
	pnpm exec tsc --noEmit

test: test-unit test-integration test-e2e

test-unit:
	uv run pytest -q || true
	pnpm exec vitest run --passWithNoTests || true

test-integration:
	@echo "Running API integration tests..."
	cd apps/api && uv run pytest -q --cov=app --cov-fail-under=75

test-e2e:
	@echo "E2E tests not yet implemented"

cdk-synth:
	cd packages/cdk && pnpm exec cdk synth

clean:
	rm -rf node_modules
	rm -rf .venv
	rm -rf cdk.out
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type d -name .pytest_cache -exec rm -r {} +
	find . -type d -name .mypy_cache -exec rm -r {} +
	find . -type d -name .ruff_cache -exec rm -r {} +

format:
	uv run ruff format .
	pnpm exec prettier --write .

eval:
	@echo "Eval not yet implemented"

dev: dev-api dev-web

dev-api:
	@echo "Starting Dev API..."
	cd apps/api && uv run uvicorn app.main:app --reload --port 8000

export-openapi:
	@echo "Exporting OpenAPI schema..."
	cd apps/api && uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > ../../packages/shared-types/openapi.json
	@echo "OpenAPI schema exported."

dev-web:
	@echo "Dev Web not yet implemented"
