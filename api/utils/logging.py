"""
Angles OS™ Logging Configuration
Structured logging with loguru
"""
import sys
from loguru import logger
from api.config import settings

# Remove default handler
logger.remove()

# Add console handler with pretty formatting
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True
)

# Add file handler with rotation
logger.add(
    "app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.log_level,
    rotation="10 MB",
    retention="1 week",
    compression="gz"
)

# Export configured logger
__all__ = ['logger']