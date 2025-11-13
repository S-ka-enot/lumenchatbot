from __future__ import annotations

__all__ = ["run"]


def run() -> None:
    """Запуск Telegram-бота."""
    from .main import run as _run

    _run()
