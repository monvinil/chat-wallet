"""
Centralized logging configuration for Chat Wallet

Provides consistent logging across all modules with appropriate levels:
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages (something unexpected but handled)
- ERROR: Error messages (functionality affected)
- CRITICAL: Critical issues (app may crash)
"""

import logging
import sys
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "chat_wallet") -> logging.Logger:
    """
    Get or create logger instance

    Args:
        name: Logger name (defaults to 'chat_wallet')

    Returns:
        Configured logger instance
    """
    global _logger

    if _logger is None:
        _logger = logging.getLogger(name)

        # Set level from environment or default to INFO
        import os
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        _logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        _logger.addHandler(handler)

        # Prevent duplicate logs
        _logger.propagate = False

    return _logger


# Convenience module-level logger
logger = get_logger()
