# backend/core/logger.py
import logging
import sys

# Configure standard python logging for enterprise use
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger instance for the given module name."""
    return logging.getLogger(name)
