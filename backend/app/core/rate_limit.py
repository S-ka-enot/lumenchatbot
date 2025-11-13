from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Создаем экземпляр лимитера
limiter = Limiter(key_func=get_remote_address)


def get_rate_limit_config() -> dict[str, str]:
    """
    Возвращает конфигурацию rate limiting для разных эндпоинтов.
    
    Формат: "количество запросов/период"
    Примеры:
    - "5/minute" - 5 запросов в минуту
    - "100/hour" - 100 запросов в час
    - "1000/day" - 1000 запросов в день
    """
    return {
        # Аутентификация - строгие лимиты для защиты от brute-force
        "/api/v1/auth/login": "5/minute",
        
        # Общие эндпоинты - умеренные лимиты
        "/api/v1/subscribers": "100/minute",
        "/api/v1/payments": "100/minute",
        "/api/v1/channels": "100/minute",
        "/api/v1/subscription-plans": "100/minute",
        "/api/v1/bots": "50/minute",
        "/api/v1/settings": "50/minute",
        "/api/v1/dashboard": "30/minute",
        
        # Bot API - более мягкие лимиты для пользователей бота
        "/api/v1/bot": "200/minute",
        
        # Webhook YooKassa - отдельный лимит
        "/api/v1/payments/yookassa/webhook": "100/minute",
    }


def get_default_rate_limit() -> str:
    """Возвращает дефолтный лимит для всех остальных эндпоинтов."""
    return "100/minute"

