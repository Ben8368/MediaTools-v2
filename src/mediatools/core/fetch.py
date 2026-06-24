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
    strip_subtitle_language_suffix,
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
    template: FetchOptions,
) -> list[FetchOptions]:
    """Create per-URL fetch options from a shared template.

    Each URL gets its own ``FetchOptions`` with all other fields copied
    from *template*.  The ``FetchOptions`` dataclass defaults are the
    single source of truth for every field default.
    """
    if not urls:
        raise MediaToolsError("Provide a fetch URL or --input-file with at least one URL.")
    return [replace(template, url=url) for url in urls]


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
    result = run_ytdlp(build_fetch_args(normalized_options), timeout=timeout, **kwargs)
    strip_subtitle_language_suffix(output_dir)
    return result


def _fetch_one(
    options: FetchOptions,
    *,
    runner: ProcessRunner | None = None,
    timeout: float | None = None,
) -> FetchItemResult:
    """Execute a single download, always returning a result (never raises).

    ``KeyboardInterrupt`` and ``MediaToolsError`` are caught internally so
    that callers — including concurrent executors — always receive a
    ``FetchItemResult``.
    """
    try:
        resolved = _resolve_sub_langs(options)
        resolved = _resolve_filename_language(resolved, runner=runner)
        result = fetch_media(resolved, runner=runner, timeout=timeout)
        return FetchItemResult(
            url=resolved.url,
            status="succeeded",
            output_dir=normalize(options.output_dir),
            command=result.command,
        )
    except KeyboardInterrupt:
        return FetchItemResult(
            url=options.url,
            status="failed",
            output_dir=normalize(options.output_dir),
            command=("yt-dlp", *build_fetch_args(options)),
            error="Interrupted by user. Partial download files may remain.",
        )
    except MediaToolsError as exc:
        return FetchItemResult(
            url=options.url,
            status="failed",
            output_dir=normalize(options.output_dir),
            command=("yt-dlp", *build_fetch_args(options)),
            error=exc.message,
        )


def fetch_many(
    options_list: list[FetchOptions],
    *,
    dry_run: bool = False,
    runner: ProcessRunner | None = None,
    timeout: float | None = None,
    max_workers: int = 1,
) -> FetchBatchResult:
    """Run or plan multiple fetch operations.

    Args:
        options_list: One ``FetchOptions`` per URL.
        dry_run: When ``True``, build planned items without calling yt-dlp.
        runner: Optional subprocess runner for testing.
        timeout: Per-download timeout forwarded to yt-dlp.
        max_workers: Maximum concurrent downloads (default 1, serial).
            Values > 1 use a ``ThreadPoolExecutor``.
    """
    if not options_list:
        raise MediaToolsError("Provide at least one fetch URL.")

    if dry_run:
        return FetchBatchResult(items=tuple(dry_run_fetch(o) for o in options_list))

    if max_workers <= 1:
        return _fetch_serial(options_list, runner=runner, timeout=timeout)

    return _fetch_parallel(options_list, runner=runner, timeout=timeout, max_workers=max_workers)


def _fetch_serial(
    options_list: list[FetchOptions],
    *,
    runner: ProcessRunner | None = None,
    timeout: float | None = None,
) -> FetchBatchResult:
    """Run downloads one at a time, stopping on ``KeyboardInterrupt``."""
    results: list[FetchItemResult] = []
    for options in options_list:
        result = _fetch_one(options, runner=runner, timeout=timeout)
        results.append(result)
        if result.error and "Interrupted by user" in str(result.error):
            break
    return FetchBatchResult(items=tuple(results))


def _fetch_parallel(
    options_list: list[FetchOptions],
    *,
    runner: ProcessRunner | None = None,
    timeout: float | None = None,
    max_workers: int,
) -> FetchBatchResult:
    """Run downloads concurrently via ``ThreadPoolExecutor``."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results_map: dict[str, FetchItemResult] = {}
    interrupted = False

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(_fetch_one, opts, runner=runner, timeout=timeout): opts.url
            for opts in options_list
        }
        try:
            for future in as_completed(future_to_url):
                try:
                    results_map[future_to_url[future]] = future.result()
                except Exception:
                    results_map[future_to_url[future]] = FetchItemResult(
                        url=future_to_url[future],
                        status="failed",
                        output_dir=Path("."),
                        command=(),
                        error="Unexpected error during fetch.",
                    )
        except KeyboardInterrupt:
            interrupted = True
            for future in future_to_url:
                future.cancel()

    # Reconstitute results in original order, filling in gaps from interruption
    results: list[FetchItemResult] = []
    for opts in options_list:
        if opts.url in results_map:
            results.append(results_map[opts.url])
        elif interrupted:
            results.append(
                FetchItemResult(
                    url=opts.url,
                    status="failed",
                    output_dir=normalize(opts.output_dir),
                    command=("yt-dlp", *build_fetch_args(opts)),
                    error="Interrupted by user. Partial download files may remain.",
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
