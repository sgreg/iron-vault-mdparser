"""Package-wide logger configuration.

This module exposes a named `logger` instance for consistent logging across the
`ironvaultmd` package. Import and use `logger` in other modules instead of
creating new loggers to keep formatting and configuration centralized.
"""

from logging import Logger, getLogger

logger_name = "ironvaultmd"
"""The shared logger name used across the package."""

logger: Logger = getLogger(logger_name)
"""The package-level logger instance bound to `logger_name`."""
