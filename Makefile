# Makefile
.PHONY: help install test lint format run-dev run-prod docker-build docker-up docker-down migrate

help:
	@echo "Available commands:"
	@echo "  install       Install dependencies"
	@echo "  test          Run tests"
	@echo "  lint          Run linting"
	@echo "  format        Format code"
	@echo "  run-dev       Run development server"
	@echo "  run-prod      Run production server"
	@echo "  docker-build  Build Docker images"
	@echo "  docker-up     Start Docker containers"
	@echo "  docker-down   Stop Docker containers"
	@echo "  migrate       Run database migrations"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v --cov=api --cov-report=html

lint:
	flake8 api/ agents/ --max-line-length=100
	mypy api/ agents/ --ignore-missing-imports

format:
	black api/ agents/ tests/ --line-length=100

run-dev:
	FLASK_ENV=development python -m api.main

run-prod:
	gunicorn -w 4 -b 0.0.0.0:5000 --worker-class aiohttp.GunicornWebWorker api.main:create_app

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	flask db upgrade

init-db:
	flask db init
	flask db migrate -m "Initial migration"
	flask db upgrade

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/

monitoring-up:
	docker-compose up -d prometheus grafana

monitoring-down:
	docker-compose stop prometheus grafana

logs:
	docker-compose logs -f

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

deploy-k8s:
	kubectl apply -f kubernetes/

scale-api:
	kubectl scale deployment financial-api --replicas=5 -n financial-platform

# CI/CD commands
ci-test:
	@echo "Running CI tests..."
	make lint
	make test
	@echo "CI tests passed!"

ci-build:
	@echo "Building for CI..."
	docker build -t financial-platform/api:$(VERSION) .
	docker build -t financial-platform/websocket:$(VERSION) -f Dockerfile.websocket .

ci-push:
	@echo "Pushing to registry..."
	docker push financial-platform/api:$(VERSION)
	docker push financial-platform/websocket:$(VERSION)
