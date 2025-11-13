POETRY ?= poetry
PYTHON ?= python

.PHONY: install install-dev backend bot frontend dev migrate lint format test stop-services

install:
	$(POETRY) install --no-root

install-dev:
	$(POETRY) install

backend:
	$(POETRY) run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

dev: install backend

migrate:
	$(POETRY) run alembic upgrade head

lint:
	$(POETRY) run ruff check backend

format:
	$(POETRY) run ruff check backend --select I --fix
	$(POETRY) run black backend

test:
	$(POETRY) run pytest

bot:
	$(POETRY) run python -m bot.app.main

frontend:
	cd frontend && npm run dev

start-all: install-dev
	@if [ ! -f config/env.local ]; then \
		cp config/env.example config/env.local; \
		echo "Created config/env.local"; \
	fi
	@if [ ! -d frontend/node_modules ]; then \
		cd frontend && npm install; \
	fi
	$(POETRY) run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 & \
	$(POETRY) run python -m bot.app.main > bot.log 2>&1 & \
	cd frontend && npm run dev > ../frontend-dev.log 2>&1 & \
	echo "All services started. Check logs:"
	echo "Backend: tail -f backend.log"
	echo "Bot: tail -f bot.log"
	echo "Frontend: tail -f frontend-dev.log"

stop-services:
	pkill -f "uvicorn backend.app.main:app" || true
	pkill -f "python -m bot.app.main" || true
	pkill -f "npm run dev" || true
	echo "All services stopped"

