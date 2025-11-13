# ✅ Финальное решение для Bot в Coolify

## 🔍 Проблема

Backend работает с:
- Base Directory = `/`
- Dockerfile Location = `/Dockerfile` (корневой Dockerfile)

Но Bot не работает с:
- Base Directory = `/`
- Dockerfile Location = `/bot/Dockerfile`

## ✅ Решение: Использовать корневой Dockerfile для Bot

Создан файл `Dockerfile.bot` в корне проекта, аналогично `Dockerfile` для Backend.

### Настройки для Bot в Coolify:

1. **Base Directory:** `/`
2. **Dockerfile Location:** `/Dockerfile.bot` (аналогично `/Dockerfile` для Backend)
3. **Docker Build Stage Target:** пусто

## 📋 Пошаговая инструкция

1. Откройте Bot сервис в Coolify
2. Перейдите в "General" → "Build"
3. Установите:
   - **Base Directory:** `/`
   - **Dockerfile Location:** `/Dockerfile.bot`
   - **Docker Build Stage Target:** очистите (оставьте пустым)
4. Нажмите "Save"
5. Нажмите "Deploy"

## 🔍 Почему это работает

- Backend использует `/Dockerfile` (корневой) с Build Context = корень проекта
- Bot теперь использует `/Dockerfile.bot` (корневой) с Build Context = корень проекта
- Оба Dockerfile находятся в корне проекта и ожидают Build Context = корень проекта
- Coolify с Base Directory = `/` устанавливает Build Context = корень проекта

## ✅ Проверка

После изменений в логах должно быть:
```
#8 [base 4/5] COPY backend/pyproject.toml backend/poetry.lock ./
#8 DONE (успешно!)
```

Вместо ошибки `"/backend/poetry.lock": not found`.

