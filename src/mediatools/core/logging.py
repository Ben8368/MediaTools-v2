"""Structured logging for MediaTools.

The logging system provides a simple interface for emitting structured log messages
at different severity levels. The actual output format and destination are controlled
by the CLI layer.
"""

from __future__ import annotations

import sys
from enum import IntEnum
from typing import Any, Protocol


class LogLevel(IntEnum):
    """Log severity levels."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


class LogHandler(Protocol):
    """Protocol for log message handlers."""

    def emit(self, level: LogLevel, message: str, **context: Any) -> None:
        """Emit a log message with optional context."""
        ...


class Logger:
    """Structured logger that delegates output to a handler."""

    def __init__(self, handler: LogHandler, min_level: LogLevel = LogLevel.INFO) -> None:
        """Create a logger with the given handler and minimum level.

        Args:
            handler: The handler responsible for outputting log messages.
            min_level: Minimum severity level to emit (default: INFO).
        """
        self._handler = handler
        self._min_level = min_level

    def debug(self, message: str, **context: Any) -> None:
        """Log a debug message."""
        self._log(LogLevel.DEBUG, message, **context)

    def info(self, message: str, **context: Any) -> None:
        """Log an informational message."""
        self._log(LogLevel.INFO, message, **context)

    def warning(self, message: str, **context: Any) -> None:
        """Log a warning message."""
        self._log(LogLevel.WARNING, message, **context)

    def error(self, message: str, **context: Any) -> None:
        """Log an error message."""
        self._log(LogLevel.ERROR, message, **context)

    def _log(self, level: LogLevel, message: str, **context: Any) -> None:
        """Emit a log message if it meets the minimum level threshold."""
        if level >= self._min_level:
            self._handler.emit(level, message, **context)


class StreamHandler:
    """Simple handler that writes log messages to a stream."""

    def __init__(self, stream: Any = None, show_level: bool = True) -> None:
        """Create a stream handler.

        Args:
            stream: Output stream (default: sys.stderr).
            show_level: Whether to prefix messages with the log level.
        """
        self._stream = stream if stream is not None else sys.stderr
        self._show_level = show_level

    def emit(self, level: LogLevel, message: str, **context: Any) -> None:
        """Write a log message to the stream."""
        parts = []
        if self._show_level:
            parts.append(f"[{level.name}]")
        parts.append(message)
        if context:
            context_str = " ".join(f"{k}={v!r}" for k, v in context.items())
            parts.append(f"({context_str})")

        line = " ".join(parts)
        print(line, file=self._stream)
