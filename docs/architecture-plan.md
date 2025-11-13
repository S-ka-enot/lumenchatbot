## План архитектуры проекта LumenPay Bot

### 1. Общая структура репозитория

- `backend/` — асинхронный REST API на FastAPI. Содержит бизнес-логику, ORM‑модели, фоновые задачи и интеграции с платежными провайдерами.
- `bot/` — Telegram-бот на `python-telegram-bot`, использует REST API бэкенда и совместную модель данных.
- `frontend/` — административная панель на React 18, TypeScript и Vite с Tailwind CSS и shadcn/ui.
- `infra/` — конфигурации Docker/Docker Compose, Nginx, reverse proxy, CI/CD шаблоны.
- `docs/` — документация (план, схемы, инструкции по деплою, API).
- `scripts/` — утилиты для инициализации БД, загрузки тестовых данных и запуска фоновых задач.
- `tests/` — разделенные по подсистемам автоматические тесты (backend, bot, e2e).
- `Makefile` — быстрые команды для разработки (линт, тесты, запуск сервисов).
- `pyproject.toml`, `package.json`, `.pre-commit-config.yaml`, `.env.example`, `.editorconfig` — общие настройки проекта.

### 2. Архитектура backend сервиса

- **FastAPI** с `uvicorn` и `gunicorn` (для production).
- **Слой API** — маршруты в `/app/api/v1`, с зависимостями для аутентификации (JWT + session cookies).
- **Слой сервисов** — бизнес-логика (модули: users, subscriptions, payments, promocodes, broadcasts, bots, channels).
- **Слой данных**:
  - SQLAlchemy ORM (async engine) + Alembic миграции (`backend/app/db`).
  - Схемы Pydantic (`backend/app/schemas`).
  - Конфигурация через Pydantic Settings (`backend/app/core/config.py`).
- **Внешние интеграции**:
  - YooKassa SDK (REST) — модуль `backend/app/integrations/yookassa`.
  - Telegram Bot API — вспомогательные методы (для invite ссылок).
- **Фоновые задачи**:
  - APScheduler (asyncio) для периодических задач.
  - Отдельные воркеры в модуле `backend/app/background`.
- **Безопасность**:
  - bcrypt через `passlib`.
  - Fernet для хранения токенов Telegram (в таблице `bots`).
  - Rate limiting через `slowapi` или middleware (опционально).

### 3. Архитектура Telegram-бота

- `python-telegram-bot` v20+ (asyncio).
- Основные сценарии вынесены в handler-модули:
  - `commands/start.py`, `commands/buy.py`, `commands/status.py`, `commands/channels.py`, `commands/help.py`.
- Сервисный слой `bot/services` вызывает REST API backend-а (`/api/...`) через HTTP клиент `httpx`.
- Обработка платежей:
  - Создание invoice через backend (`POST /api/payments/create`), который общается с YooKassa.
  - Вебхуки YooKassa приходят в backend, который уведомляет бот (через queue/API).
- Очереди/уведомления:
  - Использование Redis (опционально) для передачи задач между backend и ботом.
  - Fallback — прямые запросы бота к API на cron-задачах.

### 4. Админ-панель (frontend)

- React 18 + TypeScript + Vite.
- Tailwind CSS + shadcn/ui (Radix UI primitives).
- React Router v6 для маршрутизации.
- React Query для работы с API (`/api/*`), Axios как транспорт.
- Структура:
  - `src/pages` — страницы (Dashboard, Users, Channels, PromoCodes, Broadcasts, Settings, Auth).
  - `src/components` — UI компоненты + таблицы, графики (Recharts).
  - `src/hooks` — custom hooks для API.
  - `src/store` — глобальные настройки (например, аутентификация).
  - `src/lib` — вспомогательные функции.
  - `src/assets` — логотипы, иконки.
- Поддержка i18n (опционально) через React-i18next.

### 5. Инфраструктура и DevOps

- Docker Compose:
  - `backend` (FastAPI + uvicorn/gunicorn).
  - `bot` (python-telegram-bot worker).
  - `frontend` (Vite build + Nginx для выдачи статики).
  - `db` (PostgreSQL).
  - `redis` (для задач и сессий).
  - `scheduler` (отдельный процесс APScheduler или Celery Beat).
- GitHub Actions:
  - Линтинг (`ruff`, `mypy`, `eslint`, `prettier`, `stylelint`).
  - Тесты (`pytest`, frontend unit/e2e).
  - Сборка Docker образов, деплой на сервер (по тэгу).
- Nginx конфигурация для выдачи фронтенда, проксирования `/api` и бота.
- Мониторинг:
  - `infra/monitoring/` — конфиг Sentry (dsn), Prometheus (опционально).
  - Health-check endpoint `/api/health`.

### 6. База данных и миграции

- Alembic с автогенерацией миграций.
- Стартовые миграции создают таблицы, описанные в ТЗ (`bots`, `users`, `subscriptions`, `payments`, `channels`, `promo_codes`, `admins`, ` access_logs`, `bot_messages`, `scheduled_broadcasts`).
- Для development — SQLite; через `.env` переключение на PostgreSQL.
- Скрипт `scripts/seed_data.py` для загрузки тестовых пользователей, каналов и промокодов.

### 7. Процесс разработки

1. **Инициализация репозитория** — настройка окружений (Python, Node.js), базовых конфигураций.
2. **Backend MVP** — API для пользователей, подписок, платежей, базовая админ-аутентификация.
3. **Telegram Bot MVP** — команды `/start`, `/buy`, `/status`, интеграция с API.
4. **Frontend MVP** — Auth + список пользователей, базовый дашборд.
5. **Фоновые процессы** — напоминания, проверка подписок, платежей.
6. **Расширения** — промокоды, рассылки, шаблоны сообщений, аналитика.
7. **Продакшн готовность** — Docker, CI/CD, документация, тесты.

### 8. Следующие шаги

- Создать `README.md` с обзором и инструкциями по запуску.
- Настроить общие конфиги (`.env.example`, `.editorconfig`, `.gitignore`).
- Сгенерировать базовую структуру директорий для backend, bot, frontend.
- Подготовить зависимости (Poetry для Python, pnpm/npm для frontend).

