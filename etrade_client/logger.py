import logging
import os
from logging.handlers import RotatingFileHandler
from uuid import uuid4

_FORMAT = "%(asctime)-15s %(message)s"
_DATE_FMT = "%m/%d/%Y %I:%M:%S %p"
_LOGGER_NAME = "etrade_client"


def get_logger():
    """Return the shared logger, configuring file logging on first use."""
    logger = logging.getLogger(_LOGGER_NAME)
    if not any(not isinstance(handler, logging.NullHandler) for handler in logger.handlers):
        logger.setLevel(logging.DEBUG)
        log_file = f"python_client_{os.getpid()}_{uuid4().hex}.log"
        handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
        handler.setFormatter(logging.Formatter(
            _FORMAT, datefmt=_DATE_FMT
        ))
        logger.addHandler(handler)

    return logger
