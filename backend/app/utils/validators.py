from __future__ import annotations

import re
from decimal import Decimal


def validate_phone_number(phone: str | None) -> str | None:
    """Валидация номера телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX."""
    if phone is None or phone == "":
        return None

    # Удаляем все пробелы, дефисы и скобки
    cleaned = re.sub(r"[\s\-()]", "", phone)

    # Проверяем формат: +7XXXXXXXXXX или 8XXXXXXXXXX
    if cleaned.startswith("+7") and len(cleaned) == 12:
        return cleaned
    if cleaned.startswith("8") and len(cleaned) == 11:
        # Конвертируем 8XXXXXXXXXX в +7XXXXXXXXXX
        return "+7" + cleaned[1:]
    if cleaned.startswith("7") and len(cleaned) == 11:
        return "+" + cleaned

    raise ValueError(
        "Номер телефона должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX"
    )


def validate_telegram_id(telegram_id: int) -> int:
    """Валидация Telegram ID - должен быть положительным числом."""
    if telegram_id <= 0:
        raise ValueError("Telegram ID должен быть положительным числом")
    if telegram_id > 2**63 - 1:  # Максимальное значение для int64
        raise ValueError("Telegram ID слишком большой")
    return telegram_id


def validate_amount(amount: Decimal | None, min_value: Decimal | None = None) -> Decimal | None:
    """Валидация суммы платежа."""
    if amount is None:
        return None

    if amount < 0:
        raise ValueError("Сумма не может быть отрицательной")

    if min_value is not None and amount < min_value:
        raise ValueError(f"Сумма должна быть не менее {min_value}")

    # Максимальная сумма: 1 миллион рублей
    max_amount = Decimal("1000000")
    if amount > max_amount:
        raise ValueError(f"Сумма не может превышать {max_amount}")

    return amount


def validate_price_amount(amount: Decimal) -> Decimal:
    """Валидация цены тарифа."""
    if amount < 0:
        raise ValueError("Цена не может быть отрицательной")

    # Минимальная цена: 1 рубль
    min_price = Decimal("1")
    if amount < min_price:
        raise ValueError(f"Цена должна быть не менее {min_price} рубля")

    # Максимальная цена: 1 миллион рублей
    max_price = Decimal("1000000")
    if amount > max_price:
        raise ValueError(f"Цена не может превышать {max_price} рублей")

    return amount

