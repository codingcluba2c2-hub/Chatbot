# backend/core/logger.py
import logging
import sys
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Avoid adding multiple handlers if re-imported
if not logger.handlers:
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger instance for the given module name."""
    return logging.getLogger(name)
