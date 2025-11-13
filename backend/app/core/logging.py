from __future__ import annotations

import logging
from logging.config import dictConfig

import structlog

from .config import settings


def configure_logging() -> None:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer() if settings.environment == "development" else structlog.processors.JSONRenderer(),
                "foreign_pre_chain": [
                    structlog.contextvars.merge_contextvars,
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.add_log_level,
                ],
            },
        },
        "handlers": {
            "default": {
                "level": settings.log_level,
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
        },
        "loggers": {
            "": {"handlers": ["default"], "level": settings.log_level, "propagate": False},
            "uvicorn": {"handlers": ["default"], "level": settings.log_level, "propagate": False},
            "uvicorn.access": {"handlers": ["default"], "level": settings.log_level, "propagate": False},
            "lumenpay": {"handlers": ["default"], "level": settings.log_level, "propagate": False},
        },
    }

    dictConfig(logging_config)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
            if settings.environment == "development"
            else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

