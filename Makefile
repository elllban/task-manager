.PHONY: install dev test test-unit test-integration test-cov lint format migrate migrate-create docker-up docker-down docker-build docker-down-clean clean

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0

test: test-unit

test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	docker-compose up -d --build
	@echo "Waiting for API to be ready..."
	@for i in $$(seq 1 30); do \
		curl -sf http://localhost:8000/ > /dev/null 2>&1 && break; \
		echo "  attempt $$i..."; \
		sleep 2; \
	done
	curl -X POST http://localhost:8000/api/v1/auth/register \
		-H "Content-Type: application/json" \
		-d '{"email":"admin@cleanup.test","password":"Cleanup1!","password_confirm":"Cleanup1!"}' > /dev/null 2>&1 || true
	pytest tests/integration/ -v --tb=short; \
		EXIT_CODE=$$?; \
		docker-compose down; \
		exit $$EXIT_CODE

test-cov:
	pytest tests/unit/ -v --cov=app --cov-report=term --cov-report=html

lint:
	ruff check app/ tests/

lint-fix:
	ruff check --fix app/ tests/

format:
	ruff format app/ tests/

format-check:
	ruff format --check app/ tests/

migrate:
	alembic upgrade head
	alembic current

migrate-downgrade:
	alembic downgrade -1

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

migrate-show:
	alembic history

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down

docker-down-clean:
	docker-compose down -v

docker-logs:
	docker-compose logs -f

docker-build:
	docker-compose build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache htmlcov .coverage alembic/versions/__pycache__
