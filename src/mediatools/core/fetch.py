"""yt-dlp based video and subtitle download wrapper."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch_auth import build_auth_args, redact_cookies
from mediatools.core.fetch_naming import (
    build_output_template,
    prune_original_subtitle_fallbacks,
    strip_subtitle_language_suffix,
)
from mediatools.core.fetch_postprocess import (
    changed_subtitles,
    output_dir_lock,
    subtitle_snapshot,
)
from mediatools.core.fetch_resolution import (
    probe_language,
)
from mediatools.core.fetch_resolution import (
    resolve_filename_language as _resolve_filename_language,
)
from mediatools.core.fetch_resolution import (
    resolve_sub_langs as _resolve_sub_langs,
)
from mediatools.core.fetch_types import (
    FetchBatchResult,
    FetchItemResult,
    FetchOptions,
    copy_options,
    validate_url,
)
from mediatools.core.fetch_transcode import needs_transcode, transcode_if_needed
from mediatools.core.ffmpeg import ProcessRunner, ToolResult, run_ytdlp
from mediatools.core.paths import normalize
from mediatools.core.subtitle import clean_subtitle_file

_MEDIA_EXTENSIONS: frozenset[str] = frozenset({
    ".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".m4a",
    ".mp3", ".opus", ".ogg", ".wav", ".aac", ".flac",
})


def _newest_media_file(output_dir: Path) -> Path | None:
    """Return the most recently modified media file in *output_dir*.

    Scans for common media extensions and returns the newest by mtime.
    Returns ``None`` when no media files are found.
    """
    newest: Path | None = None
    newest_mtime = -1.0
    for child in output_dir.iterdir():
        if child.is_file() and child.suffix.lower() in _MEDIA_EXTENSIONS:
            try:
                mtime = child.stat().st_mtime
            except OSError:
                continue
            if mtime > newest_mtime:
                newest_mtime = mtime
                newest = child
    return newest


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
        build_auth_args(
            cookies=options.cookies,
            cookies_from_browser=options.cookies_from_browser,
        ),
    )
    if options.preset and not options.subtitles_only:
        args.extend(["-t", options.preset])
    if options.merge_format:
        args.extend(["--merge-output-format", options.merge_format])
    if options.remux_video:
        args.extend(["--remux-video", options.remux_video])
    if options.format_sort:
        args.extend(["-S", options.format_sort])
    write_subtitles, write_auto_subtitles = _effective_subtitle_flags(options)
    if write_subtitles:
        args.extend(["--write-subs", "--sub-langs", options.subtitle_languages])
    if write_auto_subtitles:
        args.append("--write-auto-subs")
        if not write_subtitles:
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


def _effective_subtitle_flags(options: FetchOptions) -> tuple[bool, bool]:
    """Return manual/automatic subtitle flags after subtitle-only defaults."""
    if not options.subtitles_only:
        return options.write_subtitles, options.write_auto_subtitles
    if options.write_subtitles or options.write_auto_subtitles:
        return options.write_subtitles, options.write_auto_subtitles
    return True, True


def load_fetch_urls(input_file: str | Path) -> list[str]:
    """Load non-empty, non-comment URLs from a UTF-8 text file."""
    path = normalize(Path(input_file))
    if not path.exists():
        raise MediaToolsError(f"Fetch input file does not exist: {path}")
    if not path.is_file():
        raise MediaToolsError(f"Fetch input path is not a file: {path}")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise MediaToolsError(f"Could not read fetch input file: {path}") from exc
    urls = [
        line.strip()
        for line in text.splitlines()
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
    args = build_fetch_args(copy_options(options, output_dir=output_dir))
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
    prefer_original_subtitles: bool = False,
) -> ToolResult:
    """Run yt-dlp for a single download operation."""
    output_dir = normalize(options.output_dir)
    with output_dir_lock(output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        before = subtitle_snapshot(output_dir)
        normalized_options = copy_options(options, output_dir=output_dir)
        kwargs = {"runner": runner} if runner is not None else {}
        result = run_ytdlp(build_fetch_args(normalized_options), timeout=timeout, **kwargs)
        changed = changed_subtitles(output_dir, before)
        for subtitle in changed:
            clean_subtitle_file(subtitle)
        if prefer_original_subtitles:
            changed = prune_original_subtitle_fallbacks(output_dir, candidates=changed)
        strip_subtitle_language_suffix(output_dir, candidates=changed)
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

    Language probing runs once and feeds both subtitle resolution and
    filename-language resolution.
    """
    try:
        validate_url(options.url)
        probed_lang = probe_language(
            options.url,
            cookies=options.cookies,
            cookies_from_browser=options.cookies_from_browser,
            runner=runner,
        )
        resolved = _resolve_sub_langs(options, probed_lang=probed_lang)
        resolved = _resolve_filename_language(resolved, probed_lang=probed_lang)
        result = fetch_media(
            resolved,
            runner=runner,
            timeout=timeout,
            prefer_original_subtitles=options.subtitle_languages == "original",
        )
        if needs_transcode(resolved):
            media_file = _newest_media_file(normalize(resolved.output_dir))
            if media_file:
                transcode_if_needed(media_file, resolved, runner=runner)
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
            command=_safe_fetch_command(options),
            error="Interrupted by user. Partial download files may remain.",
        )
    except MediaToolsError as exc:
        return FetchItemResult(
            url=options.url,
            status="failed",
            output_dir=normalize(options.output_dir),
            command=_safe_fetch_command(options),
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
    """Run downloads concurrently via ``ThreadPoolExecutor``.

    **Result assembly rules:**
    1. Futures that complete (success or failure via ``_fetch_one``) populate
       ``results_map`` immediately.  ``_fetch_one`` never raises — it catches
       ``MediaToolsError`` and ``KeyboardInterrupt`` and returns a failed
       ``FetchItemResult`` instead.
    2. If an *unexpected* exception escapes ``future.result()`` (e.g. a bug
       inside ``_fetch_one``), it is caught and recorded as a failed result.
    3. On ``KeyboardInterrupt`` in the main thread, all pending futures are
       cancelled.  Any futures that were cancelled *before* producing a result
       will have no entry in ``results_map``; these gaps are filled with an
       "Interrupted by user" failed result during reconstitution.
    4. Results are returned in the original URL order, not completion order.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results_map: dict[int, FetchItemResult] = {}
    interrupted = False

    executor = ThreadPoolExecutor(max_workers=max_workers)
    future_to_index = {
        executor.submit(
            _fetch_one,
            opts,
            runner=runner,
            timeout=timeout,
        ): index
        for index, opts in enumerate(options_list)
    }
    try:
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results_map[index] = future.result()
            except Exception as exc:
                # This branch catches bugs inside _fetch_one that are NOT
                # MediaToolsError or KeyboardInterrupt (both are caught there).
                opts = options_list[index]
                results_map[index] = FetchItemResult(
                    url=opts.url,
                    status="failed",
                    output_dir=normalize(opts.output_dir),
                    command=_safe_fetch_command(opts),
                    error=f"Unexpected error during fetch: {exc}",
                )
    except KeyboardInterrupt:
        interrupted = True
        for future in future_to_index:
            future.cancel()
    finally:
        executor.shutdown(wait=not interrupted, cancel_futures=interrupted)

    # Reconstitute results in original URL order.
    # Gaps only occur for futures that were cancelled before producing any
    # result (i.e. the main-thread KeyboardInterrupt arrived first).
    results: list[FetchItemResult] = []
    for index, opts in enumerate(options_list):
        if index in results_map:
            results.append(results_map[index])
        elif interrupted:
            results.append(
                FetchItemResult(
                    url=opts.url,
                    status="failed",
                    output_dir=normalize(opts.output_dir),
                    command=_safe_fetch_command(opts),
                    error="Interrupted by user. Partial download files may remain.",
                ),
            )
    return FetchBatchResult(items=tuple(results))


def _safe_fetch_command(options: FetchOptions) -> tuple[str, ...]:
    """Return a best-effort command for failure summaries with cookie paths redacted."""
    try:
        args = build_fetch_args(options)
    except MediaToolsError:
        return ("yt-dlp",)
    return ("yt-dlp", *redact_cookies(args))
