.PHONY: help install run test clean docker-build docker-run demo

help:
	@echo "Matrix Treasury - Available Commands"
	@echo "====================================="
	@echo "install          Install dependencies"
	@echo "run              Run development server"
	@echo "test             Run all tests"
	@echo "test-coverage    Run tests with coverage report"
	@echo "demo             Run 30-day survival simulation"
	@echo "docker-build     Build Docker image"
	@echo "docker-run       Run with Docker Compose"
	@echo "docker-stop      Stop Docker services"
	@echo "clean            Clean temporary files"
	@echo "lint             Run linters"
	@echo "format           Format code"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

demo:
	python3 scripts/survival_simulation.py

docker-build:
	docker-compose build

docker-run:
	docker-compose up -d
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Grafana: http://localhost:3000"

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache htmlcov .coverage

lint:
	flake8 src tests
	mypy src --ignore-missing-imports

format:
	black src tests
	isort src tests

db-setup:
	python -c "from src.db.connection import init_db; init_db()"
