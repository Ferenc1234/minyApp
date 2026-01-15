.PHONY: help build up down logs clean restart shell db-shell migrate test lint format install prod-up prod-down dev

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start containers (development)"
	@echo "  make down         - Stop containers"
	@echo "  make logs         - View application logs"
	@echo "  make clean        - Remove containers and volumes"
	@echo "  make restart      - Restart containers"
	@echo "  make shell        - Open bash in app container"
	@echo "  make db-shell     - Open PostgreSQL shell"
	@echo "  make migrate      - Run database migrations"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make prod-up      - Start production containers"
	@echo "  make prod-down    - Stop production containers"
	@echo "  make dev          - Run app locally"

install:
	pip install -r requirements.txt

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f app

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

restart:
	docker compose restart

shell:
	docker compose exec app bash

db-shell:
	docker compose exec db psql -U mineuser -d minedb

migrate:
	docker compose exec app alembic upgrade head

prod-up:
	docker compose -f docker-compose.prod.yml up -d

prod-down:
	docker compose -f docker-compose.prod.yml down

dev:
	python main.py
