"""yt-dlp based video and subtitle download wrapper."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from mediatools.core.errors import ExternalToolError, MediaToolsError
from mediatools.core.fetch_naming import (
    AUTO_FILENAME_LANGUAGE,
    DEFAULT_FILENAME_TEMPLATE,
    build_output_template,
    template_uses_language,
    to_filename_language_code,
)
from mediatools.core.ffmpeg import ProcessRunner, ToolResult, run_ytdlp
from mediatools.core.paths import normalize


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
    preset: str | None = None
    merge_format: str | None = None
    remux_video: str | None = None
    convert_subs: str | None = None
    format_sort: str | None = None
    cookies: Path | None = None
    cookies_from_browser: str | None = None
    filename_template: str | None = DEFAULT_FILENAME_TEMPLATE
    filename_language: str | None = AUTO_FILENAME_LANGUAGE
    windows_filenames: bool = True


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


def probe_language(
    url: str,
    *,
    cookies: Path | None = None,
    cookies_from_browser: str | None = None,
    runner: ProcessRunner | None = None,
) -> str | None:
    """Return the video's primary language code, or None on failure."""
    try:
        kwargs = {"runner": runner} if runner is not None else {}
        result = run_ytdlp(
            [
                *_build_auth_args(cookies=cookies, cookies_from_browser=cookies_from_browser),
                "--print",
                "language",
                "--skip-download",
                url,
            ],
            timeout=60,
            **kwargs,
        )
    except ExternalToolError:
        return None
    for line in result.stdout.splitlines():
        lang = line.strip()
        if lang and lang != "NA":
            return lang
    return None


def _resolve_sub_langs(options: FetchOptions) -> FetchOptions:
    """Replace the 'original' magic keyword with a detected language code."""
    if options.subtitle_languages != "original":
        return options
    lang = probe_language(
        options.url,
        cookies=options.cookies,
        cookies_from_browser=options.cookies_from_browser,
    )
    if not lang:
        resolved = "all"
    elif "-" in lang:
        base = lang.split("-")[0]
        resolved = f"{lang}-orig,{lang},{base}-orig,{base}"
    else:
        resolved = f"{lang}-orig,{lang}"
    return _copy_options(options, subtitle_languages=resolved)


def _resolve_filename_language(
    options: FetchOptions,
    *,
    runner: ProcessRunner | None = None,
) -> FetchOptions:
    """Replace the automatic filename language marker with a probed short code."""
    if (options.filename_language or "").lower() != AUTO_FILENAME_LANGUAGE:
        return options
    if not template_uses_language(options.filename_template):
        return options
    lang = probe_language(
        options.url,
        cookies=options.cookies,
        cookies_from_browser=options.cookies_from_browser,
        runner=runner,
    )
    return _copy_options(options, filename_language=to_filename_language_code(lang) or "UN")


def _copy_options(options: FetchOptions, **overrides: object) -> FetchOptions:
    """Return a new FetchOptions with the given field overrides."""
    return replace(options, **overrides)


def build_fetch_args(options: FetchOptions) -> list[str]:
    """Build yt-dlp arguments for a controlled download."""
    validate_url(options.url)
    output_dir = normalize(options.output_dir)
    template = build_output_template(
        options.output_template,
        filename_template=options.filename_template,
        filename_language=options.filename_language,
    )

    args = [
        "--paths",
        str(output_dir),
        "--output",
        template,
        "--no-overwrites" if not options.overwrite else "--force-overwrites",
    ]
    if options.windows_filenames:
        args.append("--windows-filenames")
    args.extend(
        _build_auth_args(
            cookies=options.cookies,
            cookies_from_browser=options.cookies_from_browser,
        ),
    )
    if options.preset:
        args.extend(["-t", options.preset])
    if options.merge_format:
        args.extend(["--merge-output-format", options.merge_format])
    if options.remux_video:
        args.extend(["--remux-video", options.remux_video])
    if options.format_sort:
        args.extend(["-S", options.format_sort])
    if options.write_subtitles or options.subtitles_only:
        args.extend(["--write-subs", "--sub-langs", options.subtitle_languages])
    if options.write_auto_subtitles:
        args.append("--write-auto-subs")
        if not (options.write_subtitles or options.subtitles_only):
            args.extend(["--sub-langs", options.subtitle_languages])
    if options.convert_subs:
        args.extend(["--convert-subs", options.convert_subs])
    if options.subtitles_only:
        args.append("--skip-download")
    if options.write_info_json:
        args.append("--write-info-json")
    if options.download_archive is not None:
        args.extend(["--download-archive", str(normalize(options.download_archive))])
    args.append(options.url)
    return args


def load_fetch_urls(input_file: str | Path) -> list[str]:
    """Load non-empty, non-comment URLs from a UTF-8 text file."""
    path = normalize(Path(input_file))
    if not path.exists():
        raise MediaToolsError(f"Fetch input file does not exist: {path}")
    urls = [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not urls:
        raise MediaToolsError(f"Fetch input file has no URLs: {path}")
    for url in urls:
        validate_url(url)
    return urls


def make_fetch_options(
    urls: list[str],
    *,
    output_dir: Path,
    output_template: str | None = None,
    write_subtitles: bool = False,
    write_auto_subtitles: bool = False,
    subtitles_only: bool = False,
    subtitle_languages: str = "all",
    overwrite: bool = False,
    write_info_json: bool = False,
    download_archive: Path | None = None,
    preset: str | None = None,
    merge_format: str | None = None,
    remux_video: str | None = None,
    convert_subs: str | None = None,
    format_sort: str | None = None,
    cookies: Path | None = None,
    cookies_from_browser: str | None = None,
    filename_template: str | None = DEFAULT_FILENAME_TEMPLATE,
    filename_language: str | None = AUTO_FILENAME_LANGUAGE,
    windows_filenames: bool = True,
) -> list[FetchOptions]:
    """Create per-URL fetch options from shared CLI settings."""
    if not urls:
        raise MediaToolsError("Provide a fetch URL or --input-file with at least one URL.")
    return [
        FetchOptions(
            url=url,
            output_dir=output_dir,
            output_template=output_template,
            write_subtitles=write_subtitles,
            write_auto_subtitles=write_auto_subtitles,
            subtitles_only=subtitles_only,
            subtitle_languages=subtitle_languages,
            overwrite=overwrite,
            write_info_json=write_info_json,
            download_archive=download_archive,
            preset=preset,
            merge_format=merge_format,
            remux_video=remux_video,
            convert_subs=convert_subs,
            format_sort=format_sort,
            cookies=cookies,
            cookies_from_browser=cookies_from_browser,
            filename_template=filename_template,
            filename_language=filename_language,
            windows_filenames=windows_filenames,
        )
        for url in urls
    ]


def dry_run_fetch(options: FetchOptions) -> FetchItemResult:
    """Build a planned fetch item without calling yt-dlp."""
    output_dir = normalize(options.output_dir)
    args = build_fetch_args(_replace_output_dir(options, output_dir))
    return FetchItemResult(
        url=options.url,
        status="planned",
        output_dir=output_dir,
        command=("yt-dlp", *args),
    )


def fetch_media(
    options: FetchOptions,
    *,
    runner: ProcessRunner | None = None,
    timeout: float | None = None,
) -> ToolResult:
    """Run yt-dlp for a single download operation."""
    output_dir = normalize(options.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    normalized_options = _copy_options(options, output_dir=output_dir)
    kwargs = {"runner": runner} if runner is not None else {}
    return run_ytdlp(build_fetch_args(normalized_options), timeout=timeout, **kwargs)


def fetch_many(
    options_list: list[FetchOptions],
    *,
    dry_run: bool = False,
    runner: ProcessRunner | None = None,
    timeout: float | None = None,
) -> FetchBatchResult:
    """Run or plan multiple fetch operations."""
    if not options_list:
        raise MediaToolsError("Provide at least one fetch URL.")

    results: list[FetchItemResult] = []
    for options in options_list:
        if dry_run:
            results.append(dry_run_fetch(options))
            continue
        try:
            options = _resolve_sub_langs(options)
            options = _resolve_filename_language(options, runner=runner)
            result = fetch_media(options, runner=runner, timeout=timeout)
            results.append(
                FetchItemResult(
                    url=options.url,
                    status="succeeded",
                    output_dir=normalize(options.output_dir),
                    command=result.command,
                ),
            )
        except KeyboardInterrupt:
            results.append(
                FetchItemResult(
                    url=options.url,
                    status="failed",
                    output_dir=normalize(options.output_dir),
                    command=("yt-dlp", *build_fetch_args(options)),
                    error="Interrupted by user. Partial download files may remain.",
                ),
            )
            break
        except MediaToolsError as exc:
            results.append(
                FetchItemResult(
                    url=options.url,
                    status="failed",
                    output_dir=normalize(options.output_dir),
                    command=("yt-dlp", *build_fetch_args(options)),
                    error=exc.message,
                ),
            )
    return FetchBatchResult(items=tuple(results))


def validate_url(url: str) -> None:
    """Allow only explicit HTTP(S) URLs for network downloads."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise MediaToolsError("Fetch URL must be an absolute http or https URL.")


def _build_auth_args(
    *,
    cookies: Path | None,
    cookies_from_browser: str | None,
) -> list[str]:
    if cookies is not None and cookies_from_browser:
        raise MediaToolsError("Use either --cookies or --cookies-from-browser, not both.")
    if cookies is not None:
        return ["--cookies", str(normalize(cookies))]
    if cookies_from_browser:
        return ["--cookies-from-browser", cookies_from_browser]
    return []


def _replace_output_dir(options: FetchOptions, output_dir: Path) -> FetchOptions:
    return _copy_options(options, output_dir=output_dir)
