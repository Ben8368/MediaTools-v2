"""Tests for the logging system."""

from __future__ import annotations

from io import StringIO

from mediatools.core.logging import Logger, LogLevel, StreamHandler


def test_logger_respects_min_level():
    """Logger should only emit messages at or above the minimum level."""
    stream = StringIO()
    handler = StreamHandler(stream=stream, show_level=True)
    logger = Logger(handler, min_level=LogLevel.WARNING)

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")

    output = stream.getvalue()
    assert "debug message" not in output
    assert "info message" not in output
    assert "warning message" in output
    assert "error message" in output


def test_logger_emits_all_levels_when_debug():
    """Logger with DEBUG level should emit all messages."""
    stream = StringIO()
    handler = StreamHandler(stream=stream, show_level=True)
    logger = Logger(handler, min_level=LogLevel.DEBUG)

    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")

    output = stream.getvalue()
    assert "[DEBUG] debug" in output
    assert "[INFO] info" in output
    assert "[WARNING] warning" in output
    assert "[ERROR] error" in output


def test_stream_handler_includes_context():
    """Stream handler should include context key-value pairs."""
    stream = StringIO()
    handler = StreamHandler(stream=stream, show_level=False)
    logger = Logger(handler, min_level=LogLevel.INFO)

    logger.info("processing file", path="/tmp/video.mp4", size=1024)

    output = stream.getvalue()
    assert "processing file" in output
    assert "path='/tmp/video.mp4'" in output
    assert "size=1024" in output


def test_stream_handler_can_hide_level():
    """Stream handler should optionally hide log level prefix."""
    stream = StringIO()
    handler = StreamHandler(stream=stream, show_level=False)
    logger = Logger(handler, min_level=LogLevel.INFO)

    logger.info("simple message")

    output = stream.getvalue()
    assert "[INFO]" not in output
    assert "simple message" in output


def test_logger_default_level_is_info():
    """Logger should default to INFO level if not specified."""
    stream = StringIO()
    handler = StreamHandler(stream=stream, show_level=True)
    logger = Logger(handler)

    logger.debug("debug")
    logger.info("info")

    output = stream.getvalue()
    assert "debug" not in output
    assert "[INFO] info" in output
