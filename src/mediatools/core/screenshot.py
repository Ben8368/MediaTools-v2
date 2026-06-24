"""Video screenshot and frame extraction helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from mediatools.core.errors import MediaFileError, MediaToolsError
from mediatools.core.ffmpeg import ProcessRunner, ToolResult, run_ffmpeg
from mediatools.core.paths import normalize

TIME_RE = re.compile(r"^\d+(?:\.\d+)?$|^\d{1,2}:\d{2}:\d{2}(?:\.\d{1,3})?$")


@dataclass(frozen=True)
class ScreenshotOptions:
    """Options for taking one screenshot or extracting frames."""

    input_path: Path
    output_path: Path
    timestamp: str | None = None
    interval_seconds: float | None = None
    overwrite: bool = False


def build_screenshot_args(options: ScreenshotOptions) -> list[str]:
    """Build ffmpeg arguments for screenshot or frame extraction."""
    input_path = str(normalize(options.input_path))
    output_path = str(normalize(options.output_path))
    base = ["-y" if options.overwrite else "-n"]

    if options.interval_seconds is not None:
        return [
            *base,
            "-i",
            input_path,
            "-vf",
            f"fps=1/{options.interval_seconds:g}",
            output_path,
        ]

    timestamp = options.timestamp or "00:00:00"
    return [
        *base,
        "-ss",
        timestamp,
        "-i",
        input_path,
        "-frames:v",
        "1",
        output_path,
    ]


def capture_screenshot(
    options: ScreenshotOptions,
    *,
    runner: ProcessRunner | None = None,
    timeout: float | None = None,
) -> ToolResult:
    """Run ffmpeg to capture a frame or extract frames by interval."""
    input_path = normalize(options.input_path)
    output_path = normalize(options.output_path)
    _validate_options(input_path, output_path, options)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    normalized_options = ScreenshotOptions(
        input_path=input_path,
        output_path=output_path,
        timestamp=options.timestamp,
        interval_seconds=options.interval_seconds,
        overwrite=options.overwrite,
    )
    kwargs = {"runner": runner} if runner is not None else {}
    return run_ffmpeg(build_screenshot_args(normalized_options), timeout=timeout, **kwargs)


def _validate_options(input_path: Path, output_path: Path, options: ScreenshotOptions) -> None:
    if not input_path.exists():
        raise MediaFileError("Input media file does not exist.", path=str(input_path))
    if not input_path.is_file():
        raise MediaFileError("Input path is not a file.", path=str(input_path))
    if output_path.exists() and not options.overwrite:
        raise MediaFileError(
            "Output file already exists. Use --overwrite to replace it.",
            path=str(output_path),
        )
    if options.timestamp and TIME_RE.match(options.timestamp) is None:
        raise MediaToolsError("Timestamp must be seconds or HH:MM:SS[.mmm].")
    if options.interval_seconds is not None and options.interval_seconds <= 0:
        raise MediaToolsError("Interval must be greater than zero.")
