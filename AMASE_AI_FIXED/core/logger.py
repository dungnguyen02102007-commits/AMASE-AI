"""
core/logger.py
─────────────────────────────────────────────────────────────────
Structured logging using structlog.
Supports JSON output for production log aggregators (Datadog, ELK).
"""

import logging
import structlog
from config import Config


def configure_logging() -> None:
    """
    Configures structlog with optional JSON rendering.
    Call once at application startup.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
    ]

    if Config.LOG_AS_JSON:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, Config.LOG_LEVEL, logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=shared_processors,
        )
    )

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(Config.LOG_LEVEL)


def get_logger(name: str) -> structlog.BoundLogger:
    """Returns a bound logger for a given module name."""
    return structlog.get_logger(name)
