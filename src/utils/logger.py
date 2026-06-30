"""
logger.py — Centralized logging for Nifty100 project.
"""

from loguru import logger
import sys

# Remove default handler
logger.remove()

# Console handler — colored output
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="DEBUG",
    colorize=True,
)

# File handler — full logs saved
logger.add(
    "logs/nifty100.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
)

__all__ = ["logger"]