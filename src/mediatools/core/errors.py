"""Exception types for MediaTools.

Custom exceptions provide structured error information that the CLI layer
can format into user-friendly messages.
"""

from __future__ import annotations


class MediaToolsError(Exception):
    """Base exception for all MediaTools errors."""

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        """Create a MediaTools error.

        Args:
            message: Human-readable error message.
            details: Optional structured error context.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigError(MediaToolsError):
    """Configuration-related errors."""


class PathError(MediaToolsError):
    """Path validation or traversal errors."""


class ExternalToolError(MediaToolsError):
    """Errors related to external tools like ffmpeg."""

    def __init__(
        self,
        message: str,
        *,
        tool: str,
        returncode: int | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        """Create an external tool error.

        Args:
            message: Human-readable error message.
            tool: Name of the external tool (e.g., 'ffmpeg').
            returncode: Process exit code if available.
            details: Optional structured error context.
        """
        details = details or {}
        details["tool"] = tool
        if returncode is not None:
            details["returncode"] = returncode
        super().__init__(message, details=details)
        self.tool = tool
        self.returncode = returncode


class MediaFileError(MediaToolsError):
    """Errors related to media file operations."""

    def __init__(
        self,
        message: str,
        *,
        path: str | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        """Create a media file error.

        Args:
            message: Human-readable error message.
            path: Path to the problematic file if applicable.
            details: Optional structured error context.
        """
        details = details or {}
        if path is not None:
            details["path"] = path
        super().__init__(message, details=details)
        self.path = path
