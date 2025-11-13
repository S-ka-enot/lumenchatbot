# 🔧 Альтернативное решение: Изменение Dockerfile для работы с корнем проекта

## Проблема

Coolify все еще не может найти `backend/poetry.lock`, даже после изменения Base Directory. Это означает, что Build Context автоматически устанавливается в `bot/`, а не в корень проекта.

## ✅ Решение: Изменить Dockerfile

Нужно изменить `bot/Dockerfile`, чтобы он работал, когда Build Context = корень проекта (`.`).

### Вариант 1: Использовать корень проекта как Build Context

1. В Coolify для Bot сервиса:
   - **Base Directory:** `.` (корень проекта)
   - **Dockerfile Location:** `bot/Dockerfile`

2. Измените `bot/Dockerfile`:

```dockerfile
FROM python:3.10-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files (build context is project root)
COPY backend/pyproject.toml backend/poetry.lock ./

# Install Poetry and dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main --no-interaction --no-ansi

FROM python:3.10-slim

WORKDIR /app

# Copy installed packages from base
COPY --from=base /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copy source code (build context is project root)
COPY bot/ ./bot/
COPY config/ ./config/

# Create logs directory
RUN mkdir -p logs

CMD ["python", "-m", "bot.app.main"]
```

### Вариант 2: Скопировать файлы в bot/ перед сборкой

Если Coolify не позволяет установить Build Context = корень проекта, можно скопировать `backend/pyproject.toml` и `backend/poetry.lock` в `bot/` перед сборкой.

Но это не рекомендуется, так как требует изменения структуры проекта.

## 🎯 Рекомендуемое решение

Попробуйте еще раз проверить настройки в Coolify:

1. **General** → **Build**:
   - **Base Directory:** `.` (одна точка, БЕЗ `./`)
   - **Dockerfile Location:** `bot/Dockerfile` (БЕЗ `/` в начале)

2. Если это не помогает, возможно, в Coolify есть скрытое поле Build Context, которое нужно установить отдельно.

3. Или попробуйте **пересоздать сервис** с правильными настройками с самого начала.

## 🔍 Проверка

После изменений в логах должно быть:
```
#6 [internal] load build context
#6 transferring context: ... done
#8 [base 4/5] COPY backend/pyproject.toml backend/poetry.lock ./
#8 DONE (успешно!)
```

Если все еще ошибка, возможно, нужно изменить сам Dockerfile, как показано выше.

