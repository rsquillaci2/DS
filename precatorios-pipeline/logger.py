"""Logging estruturado por módulo — sucesso, volume, latência."""

import logging
import structlog
import time
from functools import wraps
from config import LOG_LEVEL, LOG_FORMAT

_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Configuração do structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer() if LOG_FORMAT == "json"
        else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        _LEVEL_MAP.get(LOG_LEVEL.upper(), logging.INFO)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_logger(module: str) -> structlog.BoundLogger:
    """Retorna logger vinculado ao módulo."""
    return structlog.get_logger(module=module)


def log_execution(module: str):
    """Decorator que loga sucesso, volume e latência de uma função de ingestão."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(module)
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                row_count = result if isinstance(result, int) else 0
                logger.info(
                    "ingest_success",
                    function=func.__name__,
                    rows=row_count,
                    latency_s=round(elapsed, 2),
                )
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(
                    "ingest_failure",
                    function=func.__name__,
                    error=str(e),
                    latency_s=round(elapsed, 2),
                )
                raise
        return wrapper
    return decorator
