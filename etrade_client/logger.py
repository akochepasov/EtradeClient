import logging
from logging.handlers import RotatingFileHandler

_LOG_FILE = "python_client.log"
_FORMAT = "%(asctime)-15s %(message)s"
_DATE_FMT = "%m/%d/%Y %I:%M:%S %p"
_LOGGER_NAME = "etrade_client"


def get_logger():
    """Return the shared logger, configuring file logging on first use."""
    logger = logging.getLogger(_LOGGER_NAME)
    if not any(not isinstance(handler, logging.NullHandler) for handler in logger.handlers):
        logger.setLevel(logging.DEBUG)
        handler = RotatingFileHandler(_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
        handler.setFormatter(logging.Formatter(
            _FORMAT, datefmt=_DATE_FMT
        ))
        logger.addHandler(handler)

    return logger
