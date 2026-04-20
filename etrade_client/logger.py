import logging
from logging.handlers import RotatingFileHandler

_LOG_FILE = "python_client.log"
_FORMAT = "%(asctime)-15s %(message)s"
_DATE_FMT = "%m/%d/%Y %I:%M:%S %p"
_LOGGER_NAME = "my_logger"


def get_logger():
    """
    Return the shared application logger, configuring it on first call.

    All modules should obtain their logger via this function instead of
    duplicating the handler/formatter setup locally.
    """
    logger = logging.getLogger(_LOGGER_NAME)

    # Guard: only add the handler once, even if the module is imported multiple times
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = RotatingFileHandler(_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
        handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FMT))
        logger.addHandler(handler)

    return logger
