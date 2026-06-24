"""yt-dlp based video and subtitle download wrapper."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from mediatools.core.errors import MediaToolsError
from mediatools.core.ffmpeg import ProcessRunner, ToolResult, run_ytdlp
from mediatools.core.paths import normalize

SAFE_TEMPLATE_RE = re.compile(r"[^A-Za-z0-9._%()/-]+")


@dataclass(frozen=True)
class FetchOptions:
    """Options for a yt-dlp download."""

    url: str
    output_dir: Path
    output_template: str = "%(title).200B.%(ext)s"
    write_subtitles: bool = False
    subtitles_only: bool = False
    subtitle_languages: str = "all"
    overwrite: bool = False


def build_fetch_args(options: FetchOptions) -> list[str]:
    """Build yt-dlp arguments for a controlled download."""
    validate_url(options.url)
    output_dir = normalize(options.output_dir)
    template = sanitize_output_template(options.output_template)

    args = [
        "--paths",
        str(output_dir),
        "--output",
        template,
        "--no-overwrites" if not options.overwrite else "--force-overwrites",
    ]
    if options.write_subtitles or options.subtitles_only:
        args.extend(["--write-subs", "--sub-langs", options.subtitle_languages])
    if options.subtitles_only:
        args.append("--skip-download")
    args.append(options.url)
    return args


def fetch_media(
    options: FetchOptions,
    *,
    runner: ProcessRunner | None = None,
    timeout: float | None = None,
) -> ToolResult:
    """Run yt-dlp for a single download operation."""
    output_dir = normalize(options.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    normalized_options = FetchOptions(
        url=options.url,
        output_dir=output_dir,
        output_template=options.output_template,
        write_subtitles=options.write_subtitles,
        subtitles_only=options.subtitles_only,
        subtitle_languages=options.subtitle_languages,
        overwrite=options.overwrite,
    )
    kwargs = {"runner": runner} if runner is not None else {}
    return run_ytdlp(build_fetch_args(normalized_options), timeout=timeout, **kwargs)


def validate_url(url: str) -> None:
    """Allow only explicit HTTP(S) URLs for network downloads."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise MediaToolsError("Fetch URL must be an absolute http or https URL.")


def sanitize_output_template(template: str) -> str:
    """Remove characters that are invalid or awkward across common filesystems."""
    cleaned = template.replace("\\", "/").replace(":", "_")
    cleaned = SAFE_TEMPLATE_RE.sub("_", cleaned)
    cleaned = cleaned.strip(" /.")
    if not cleaned:
        return "%(title).200B.%(ext)s"
    return cleaned
