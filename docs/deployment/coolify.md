# Развертывание в Coolify

> ⚠️ Все секреты из `config/env.example` приведены для разработки. Перед деплоем **обязательно** замените их на актуальные значения и удалите тестовые токены.

## 1. Требования и структура сервисов

Приложение состоит из трёх контейнеров:

1. **backend** – FastAPI + Alembic миграции
2. **bot** – Telegram-бот
3. **frontend** – статические файлы Vite + Nginx

Дополнительно требуется **Redis** и (рекомендуется) **PostgreSQL**. SQLite подходит только для локальной разработки.

## 2. Подготовка репозитория

- Обновите ветку с последними изменениями
- Убедитесь, что `.dockerignore` не исключает `poetry.lock` (уже исправлено)
- Для фронтенда добавлен `frontend/Dockerfile` и `frontend/nginx.conf`
- Бэкенд использует `backend/docker-entrypoint.sh` для автоматического применения миграций

## 3. Настройка окружения

### 3.1 Переменные backend

| Ключ | Описание |
|------|----------|
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | Любая 32+ символа (генерируйте заново) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | (опц.) время жизни JWT |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:port/db` |
| `SYNC_DATABASE_URL` | `postgresql://user:pass@host:port/db` |
| `REDIS_URL` | `redis://default:password@host:6379/0` |
| `BACKEND_CORS_ORIGINS` | JSON-список фронтенд доменов |
| `BOT_TOKEN_ENCRYPTION_KEY` | Base64-ключ длиной 32 байта |
| `TELEGRAM_BOT_TOKEN` | Токен вашего бота |
| `YOOKASSA_*` | боевые ключи YooKassa (при необходимости) |
| `SENTRY_DSN` | (опц.) url проекта |

### 3.2 Переменные bot

| Ключ | Описание |
|------|----------|
| `BOT_TOKEN` | Токен Telegram-бота |
| `BACKEND_API_BASE_URL` | `https://<backend-domain>/api/v1` |
| `BACKEND_API_TOKEN` | Сервисный токен/ключ (можно создать через БД или seed) |
| `ALLOWED_ADMIN_CHAT_IDS` | JSON-список id админ-чатов |

### 3.3 Переменные frontend

| Ключ | Значение |
|------|----------|
| `VITE_BACKEND_API_URL` | `https://<backend-domain>/api/v1` |

Настройки можно внести через Coolify → *Environment variables* для каждого сервиса.

## 4. Создание инфраструктуры в Coolify

1. **Redis**: `Create Service → Redis → Redis 7` (сгенерировать пароль, сохранить `REDIS_URL`)
2. **PostgreSQL**: `Create Service → PostgreSQL → 15+` (получить DSN, создать базу `lumenpay`)
3. **Backend**:
   - `Create Service → Dockerfile → Git Repository`
   - Repo URL: `https://github.com/<org>/lumenchatbot.git`
   - Branch: нужная (например, `main`)
   - Build: `backend/Dockerfile`
   - Entry command оставляем по умолчанию (`uvicorn …`) – миграции выполнятся через entrypoint
   - Проброс портов: `8000`
4. **Frontend**:
   - Тип: Dockerfile, путь `frontend/Dockerfile`
   - Порт: `80`
5. **Bot**:
   - Тип: Dockerfile, путь `bot/Dockerfile`
   - Запустить без публикации порта
6. Связываем сервисы с Redis/PostgreSQL через *Connected services* и прокидываем переменные.

## 5. Деплой и миграции

1. При первом деплое backend выполнит `alembic upgrade head`
2. Убедитесь по логам, что миграции прошли успешно
3. Создайте администратора (если нет) через `ADMIN_SEED_*` переменные или скрипт `scripts/reset_admin_password.py`
4. Протестируйте API: `GET /api/v1/healthz`, `POST /api/v1/auth/login`
5. После успешного деплоя можно отключить `reload` в окружении (`ENVIRONMENT=production` делает это автоматически)

## 6. Настройка доменов и HTTPS

- В Coolify назначьте домены для backend и frontend (разные поддомены)
- Включите автоматическое SSL (Let's Encrypt)
- Для SPA важно включить `try_files` – уже есть в `frontend/nginx.conf`

## 7. Чек-лист финальной проверки

- [ ] Переменные окружения без тестовых значений
- [ ] PostgreSQL и Redis подключены
- [ ] Backend отвечает `200` на `/api/v1/healthz`
- [ ] Фронтенд открывается и обращается к правильному API
- [ ] Бот стартует и успешно авторизуется в backend
- [ ] Созданы бэкапы (если нужно) и настроены `BACKUP_*`

## 8. Дополнительные рекомендации

- Храните `BOT_TOKEN_ENCRYPTION_KEY` и токен бота в секретах Coolify
- Настройте мониторинг логов (Coolify Log drains / Sentry)
- При деплое новых версий убедитесь, что alembic миграции обратимы
- Регулярно запускайте `poetry check` и `npm audit` перед релизом


