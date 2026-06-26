"""``mediatools fetch`` — download video and subtitles via yt-dlp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from mediatools.core.config import get_max_concurrent_downloads
from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch import FetchOptions, fetch_many, load_fetch_urls, make_fetch_options
from mediatools.core.fetch_auth import redact_cookies

DEFAULT_FETCH_TIMEOUT_SECONDS = 3600.0
DEFAULT_MAX_CONCURRENT_DOWNLOADS = 8


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    fetch_parser = subparsers.add_parser("fetch", help="Download video or subtitles with yt-dlp.")
    fetch_parser.add_argument("url", nargs="?", help="http(s) URL to download.")
    fetch_parser.add_argument(
        "legacy_output_dir",
        nargs="?",
        help=argparse.SUPPRESS,
    )
    fetch_parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for downloaded files (default: downloads).",
    )
    fetch_parser.add_argument(
        "--input-file",
        help="UTF-8 text file with one URL per line. Blank lines and # comments are ignored.",
    )
    fetch_parser.add_argument(
        "--output-template",
        help="Raw yt-dlp output template. Overrides the friendly name template.",
    )
    fetch_parser.add_argument(
        "--name-template",
        "--filename-template",
        dest="filename_template",
        help=(
            "Friendly filename template, e.g. "
            "'{lang}-{author}-{title}-{platform}.{ext}'."
        ),
    )
    fetch_parser.add_argument(
        "--name-language",
        "--filename-language",
        dest="filename_language",
        default="auto",
        help="Language code for {lang}: auto, KR, EN, JP, SC, TC, AR, PT, etc.",
    )
    fetch_parser.add_argument(
        "--windows-filenames",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Force yt-dlp to sanitize downloaded filenames for Windows compatibility.",
    )
    fetch_parser.add_argument("--write-subs", action="store_true", help="Download subtitles too.")
    fetch_parser.add_argument(
        "--write-auto-subs",
        action="store_true",
        help="Download automatic subtitles too.",
    )
    fetch_parser.add_argument(
        "--subtitles-only",
        action="store_true",
        help="Download subtitles only.",
    )
    fetch_parser.add_argument("--sub-langs", default="all", help="Subtitle languages for yt-dlp.")
    fetch_parser.add_argument("--overwrite", action="store_true", help="Allow overwriting outputs.")
    fetch_parser.add_argument(
        "--write-info-json",
        action="store_true",
        help="Save yt-dlp metadata JSON next to downloaded media.",
    )
    fetch_parser.add_argument(
        "--download-archive",
        help="yt-dlp archive file used to skip URLs that were already downloaded.",
    )
    fetch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan without downloading.",
    )
    fetch_parser.add_argument("--summary-json", help="Write a JSON summary to this path.")
    fetch_parser.add_argument(
        "--preset",
        default=None,
        help="yt-dlp format preset (e.g. mp4, mkv, aac). Default: mp4 (disabled when --video-codec is set).",
    )
    fetch_parser.add_argument(
        "--merge-format",
        help="Container format for stream merging (e.g. mp4, mkv).",
    )
    fetch_parser.add_argument(
        "--remux-video",
        help="Remux to container format without re-encoding.",
    )
    fetch_parser.add_argument(
        "--convert-subs",
        choices=["srt", "vtt", "ass", "lrc"],
        help="Convert downloaded subtitles to this format.",
    )
    fetch_parser.add_argument(
        "--format-sort",
        help="yt-dlp format sort expression (e.g. 'vcodec:h264,res,fps').",
    )
    fetch_parser.add_argument(
        "--cookies",
        help="Netscape cookies.txt file for sites that require login state.",
    )
    fetch_parser.add_argument(
        "--cookies-from-browser",
        help="Browser cookie source for yt-dlp (e.g. safari, chrome, firefox).",
    )
    fetch_parser.add_argument(
        "--max-concurrent",
        "--jobs",
        dest="max_workers",
        type=int,
        default=1,
        metavar="N",
        help="Maximum concurrent downloads (default: 1, serial).",
    )
    fetch_parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_FETCH_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help="Per-download timeout in seconds (default: 3600; use 0 for no limit).",
    )
    fetch_parser.add_argument(
        "--video-codec",
        help=(
            "Target video codec for post-download transcode "
            "(e.g. h264, h265, av1, libx264). Downloads highest quality first, "
            "then transcodes if the codec doesn't match."
        ),
    )
    fetch_parser.add_argument(
        "--audio-codec",
        help=(
            "Target audio codec for post-download transcode "
            "(e.g. aac, opus, mp3)."
        ),
    )
    fetch_parser.add_argument(
        "--video-bitrate",
        help="Target video bitrate for transcode (e.g. 5M, 2000k).",
    )
    fetch_parser.add_argument(
        "--audio-bitrate",
        help="Target audio bitrate for transcode (e.g. 128k, 192k).",
    )


def run(args: argparse.Namespace) -> int:
    urls, output_dir = _resolve_fetch_inputs(args)
    if args.max_workers < 1:
        raise MediaToolsError("--max-concurrent must be at least 1.")
    # Default to "mp4" preset unless --video-codec is set (then pick highest
    # quality regardless of codec so we can transcode afterward).
    effective_preset = args.preset
    if effective_preset is None:
        effective_preset = None if args.video_codec else "mp4"
    template = FetchOptions(
        url="",  # placeholder — replaced per-URL by make_fetch_options
        output_dir=output_dir,
        output_template=args.output_template,
        write_subtitles=args.write_subs,
        write_auto_subtitles=args.write_auto_subs,
        subtitles_only=args.subtitles_only,
        subtitle_languages=args.sub_langs,
        overwrite=args.overwrite,
        write_info_json=args.write_info_json,
        download_archive=Path(args.download_archive) if args.download_archive else None,
        preset=effective_preset,
        merge_format=args.merge_format,
        remux_video=args.remux_video,
        convert_subs=args.convert_subs,
        format_sort=args.format_sort,
        cookies=Path(args.cookies) if args.cookies else None,
        cookies_from_browser=args.cookies_from_browser,
        filename_template=None if args.output_template else args.filename_template,
        filename_language=args.filename_language,
        windows_filenames=args.windows_filenames,
        video_codec=args.video_codec,
        audio_codec=args.audio_codec,
        video_bitrate=args.video_bitrate,
        audio_bitrate=args.audio_bitrate,
    )
    options = make_fetch_options(urls, template)
    timeout = None if args.timeout <= 0 else args.timeout
    max_concurrent_limit = get_max_concurrent_downloads(DEFAULT_MAX_CONCURRENT_DOWNLOADS)
    safe_max_workers = min(args.max_workers, max_concurrent_limit)
    if safe_max_workers < args.max_workers:
        print(
            f"Warning: --max-concurrent reduced from {args.max_workers} to "
            f"{max_concurrent_limit} (system limit).",
            file=sys.stderr,
        )
    result = fetch_many(
        options, dry_run=args.dry_run, max_workers=safe_max_workers, timeout=timeout
    )
    payload = _redact_cookies_in_payload(result.to_dict())
    if args.summary_json:
        _write_json_file(Path(args.summary_json), payload)
    _print_fetch_summary(payload, dry_run=args.dry_run)
    return 1 if result.failed else 0


def _resolve_fetch_inputs(args: argparse.Namespace) -> tuple[list[str], Path]:
    output_dir = args.output_dir
    positional_url = args.url

    if args.legacy_output_dir:
        if output_dir is not None:
            raise MediaToolsError(
                "Use either positional output directory or --output-dir, not both."
            )
        output_dir = args.legacy_output_dir
    elif (
        args.input_file
        and positional_url
        and output_dir is None
        and _is_legacy_output_dir_candidate(positional_url)
    ):
        output_dir = positional_url
        positional_url = None

    return _fetch_urls_from_args(positional_url, args.input_file), Path(output_dir or "downloads")


def _fetch_urls_from_args(url: str | None, input_file: str | None) -> list[str]:
    urls: list[str] = []
    if url:
        urls.append(url)
    if input_file:
        urls.extend(load_fetch_urls(input_file))
    if not urls:
        raise MediaToolsError("Provide a fetch URL or --input-file.")
    return urls


def _is_legacy_output_dir_candidate(value: str) -> bool:
    parsed = urlparse(value)
    scheme = parsed.scheme.lower()
    return not scheme or (len(scheme) == 1 and value[1:2] == ":")


def _write_json_file(path: Path, payload: dict[str, object]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise MediaToolsError(f"Could not write summary JSON: {path}") from exc


def _redact_cookies_in_command(command: list[object]) -> list[object]:
    """Return a copy of command with --cookies file paths redacted."""
    return redact_cookies([str(c) for c in command])


def _redact_cookies_in_payload(payload: dict[str, object]) -> dict[str, object]:
    """Return a copy of the summary payload with cookie paths redacted in all commands."""
    items = payload.get("items", [])
    if not isinstance(items, list):
        return payload  # Graceful degradation: return unchanged payload

    redacted_items: list[dict[str, object]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        new_item = dict(item)
        command = new_item.get("command", [])
        if not isinstance(command, list):
            command = []
        new_item["command"] = _redact_cookies_in_command(command)
        redacted_items.append(new_item)

    new_payload = dict(payload)
    new_payload["items"] = redacted_items
    return new_payload


def _print_fetch_summary(payload: dict[str, object], *, dry_run: bool) -> None:
    action = "Planned" if dry_run else "Fetched"
    total = payload.get("total", 0)
    succeeded = payload.get("succeeded", 0)
    failed = payload.get("failed", 0)
    planned = payload.get("planned", 0)
    print(
        f"{action} {total} item(s): "
        f"{succeeded} succeeded, {failed} failed, "
        f"{planned} planned.",
    )
    items = payload.get("items", [])
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        status = item.get("status", "unknown")
        url = item.get("url", "")
        print(f"- {status}: {url}")
        if dry_run:
            command = _redact_cookies_in_command(item.get("command", []))
            if isinstance(command, list):
                print(f"  command: {' '.join(str(part) for part in command)}")
        if item.get("error"):
            print(f"  error: {item['error']}", file=sys.stderr)
