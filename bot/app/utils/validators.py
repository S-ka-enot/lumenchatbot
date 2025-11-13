from __future__ import annotations

import re
from datetime import date, datetime

from dateutil import parser

PHONE_REGEX = re.compile(r"^\+7\d{10}$")


def normalize_phone(raw_phone: str) -> str | None:
    digits = re.sub(r"\D", "", raw_phone)
    if not digits:
        return None

    if len(digits) == 11 and digits.startswith(("7", "8")):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = f"7{digits}"
    elif len(digits) == 12 and digits.startswith("007"):
        digits = digits[-11:]
    elif len(digits) != 11 or not digits.startswith("7"):
        return None

    normalized = f"+{digits}"
    if not PHONE_REGEX.fullmatch(normalized):
        return None
    return normalized


def validate_phone(raw_phone: str) -> bool:
    return normalize_phone(raw_phone) is not None


def parse_birthday(raw_value: str) -> date | None:
    try:
        parsed_date = parser.parse(raw_value, dayfirst=True, yearfirst=False).date()
    except (ValueError, TypeError):
        return None

    today = datetime.now().date()
    if parsed_date > today:
        return None
    return parsed_date

