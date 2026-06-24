"""Tests for error handling."""

from __future__ import annotations

import pytest

from mediatools.core.errors import (
    ConfigError,
    ExternalToolError,
    MediaFileError,
    MediaToolsError,
    PathError,
)


def test_base_error_stores_message():
    """MediaToolsError should store the error message."""
    error = MediaToolsError("something went wrong")
    assert error.message == "something went wrong"
    assert str(error) == "something went wrong"


def test_base_error_stores_details():
    """MediaToolsError should store optional details."""
    error = MediaToolsError("error", details={"code": 42, "reason": "timeout"})
    assert error.details == {"code": 42, "reason": "timeout"}


def test_base_error_defaults_to_empty_details():
    """MediaToolsError should default to empty details dict."""
    error = MediaToolsError("error")
    assert error.details == {}


def test_config_error_is_mediatoolserror():
    """ConfigError should inherit from MediaToolsError."""
    error = ConfigError("invalid config")
    assert isinstance(error, MediaToolsError)
    assert error.message == "invalid config"


def test_path_error_is_mediatoolserror():
    """PathError should inherit from MediaToolsError."""
    error = PathError("path traversal detected")
    assert isinstance(error, MediaToolsError)
    assert error.message == "path traversal detected"


def test_external_tool_error_stores_tool_name():
    """ExternalToolError should store the tool name."""
    error = ExternalToolError("ffmpeg not found", tool="ffmpeg")
    assert error.tool == "ffmpeg"
    assert error.details["tool"] == "ffmpeg"


def test_external_tool_error_stores_returncode():
    """ExternalToolError should store the process return code."""
    error = ExternalToolError("ffmpeg failed", tool="ffmpeg", returncode=127)
    assert error.returncode == 127
    assert error.details["returncode"] == 127


def test_external_tool_error_returncode_optional():
    """ExternalToolError should work without a return code."""
    error = ExternalToolError("tool missing", tool="yt-dlp")
    assert error.returncode is None
    assert "returncode" not in error.details


def test_media_file_error_stores_path():
    """MediaFileError should store the file path."""
    error = MediaFileError("file not found", path="/tmp/video.mp4")
    assert error.path == "/tmp/video.mp4"
    assert error.details["path"] == "/tmp/video.mp4"


def test_media_file_error_path_optional():
    """MediaFileError should work without a path."""
    error = MediaFileError("unknown media error")
    assert error.path is None
    assert "path" not in error.details


def test_errors_can_be_caught_as_base_type():
    """All custom errors should be catchable as MediaToolsError."""
    errors = [
        ConfigError("config"),
        PathError("path"),
        ExternalToolError("tool", tool="ffmpeg"),
        MediaFileError("file"),
    ]

    for error in errors:
        with pytest.raises(MediaToolsError):
            raise error
