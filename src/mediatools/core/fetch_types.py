"""Fetch operation types — options, results, and URL validation.

These types are separated from the execution machinery so that consumers
of the data structures don't pull in subprocess and threading imports.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch_naming import (
    AUTO_FILENAME_LANGUAGE,
    DEFAULT_FILENAME_TEMPLATE,
)


@dataclass(frozen=True)
class FetchOptions:
    """Options for a yt-dlp download."""

    url: str
    output_dir: Path
    output_template: str | None = None
    write_subtitles: bool = False
    write_auto_subtitles: bool = False
    subtitles_only: bool = False
    subtitle_languages: str = "all"
    overwrite: bool = False
    write_info_json: bool = False
    download_archive: Path | None = None
    preset: str | None = "mp4"
    merge_format: str | None = None
    remux_video: str | None = None
    convert_subs: str | None = None
    format_sort: str | None = None
    cookies: Path | None = None
    cookies_from_browser: str | None = None
    filename_template: str | None = DEFAULT_FILENAME_TEMPLATE
    filename_language: str | None = AUTO_FILENAME_LANGUAGE
    windows_filenames: bool = True
    video_codec: str | None = None
    audio_codec: str | None = None
    video_bitrate: str | None = None
    audio_bitrate: str | None = None


FetchStatus = Literal["planned", "succeeded", "failed"]


@dataclass(frozen=True)
class FetchItemResult:
    """Result for one planned or executed fetch item."""

    url: str
    status: FetchStatus
    output_dir: Path
    command: tuple[str, ...]
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable result payload."""
        return {
            "url": self.url,
            "status": self.status,
            "output_dir": str(self.output_dir),
            "command": list(self.command),
            "error": self.error,
        }


@dataclass(frozen=True)
class FetchBatchResult:
    """Summary for a batch of fetch operations."""

    items: tuple[FetchItemResult, ...]

    @property
    def total(self) -> int:
        """Number of items in the batch."""
        return len(self.items)

    @property
    def succeeded(self) -> int:
        """Number of successful downloads."""
        return sum(1 for item in self.items if item.status == "succeeded")

    @property
    def failed(self) -> int:
        """Number of failed downloads."""
        return sum(1 for item in self.items if item.status == "failed")

    @property
    def planned(self) -> int:
        """Number of dry-run planned downloads."""
        return sum(1 for item in self.items if item.status == "planned")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable summary payload."""
        return {
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "planned": self.planned,
            "items": [item.to_dict() for item in self.items],
        }


def validate_url(url: str) -> None:
    """Allow only explicit HTTP(S) URLs for network downloads."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise MediaToolsError("Fetch URL must be an absolute http or https URL.")


def copy_options(options: FetchOptions, **overrides: object) -> FetchOptions:
    """Return a new FetchOptions with the given field overrides."""
    return replace(options, **overrides)
