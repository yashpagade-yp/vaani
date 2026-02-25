"""
logger.py — Centralized Logging
=================================
Sets up Loguru as the app-wide logger.
Loguru is much simpler than Python's built-in logging module.

Usage:
    from core.logger import logger
    logger.info("Server started")
    logger.error("Something went wrong")
    logger.debug("Pipeline created for session: {id}", id=session_id)
"""

import sys
from loguru import logger


def setup_logger(debug: bool = True) -> None:
    """
    Configure the global logger.
    Call this once at app startup in main.py.

    Args:
        debug: If True, shows DEBUG level logs. If False, only INFO and above.
    """
    # Remove the default Loguru handler
    logger.remove()

    # Set log level based on debug mode
    log_level = "DEBUG" if debug else "INFO"

    # Add a pretty console handler
    # Format: time | level | file:line | message
    logger.add(
        sys.stdout,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Optionally add a file handler for persistent logs
    logger.add(
        "logs/vaani.log",
        level="INFO",
        rotation="10 MB",    # Create new file when current reaches 10MB
        retention="7 days",  # Keep logs for 7 days
        compression="zip",   # Compress old log files
        format="{time} | {level} | {name}:{line} | {message}",
    )

    logger.info("Logger initialized | level={}", log_level)


# Export the logger — import this in every file that needs logging
__all__ = ["logger", "setup_logger"]
