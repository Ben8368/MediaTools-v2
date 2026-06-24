"""``mediatools fetch`` — download video and subtitles via yt-dlp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch import FetchOptions, fetch_many, load_fetch_urls, make_fetch_options


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    fetch_parser = subparsers.add_parser("fetch", help="Download video or subtitles with yt-dlp.")
    fetch_parser.add_argument("url", nargs="?", help="http(s) URL to download.")
    fetch_parser.add_argument("output_dir", help="Directory for downloaded files.")
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
        default="mp4",
        help="yt-dlp format preset (e.g. mp4, mkv, aac).",
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
        default=None,
        metavar="SECONDS",
        help="Per-download timeout in seconds (default: no limit).",
    )


def run(args: argparse.Namespace) -> int:
    urls = _fetch_urls_from_args(args)
    template = FetchOptions(
        url="",  # placeholder — replaced per-URL by make_fetch_options
        output_dir=Path(args.output_dir),
        output_template=args.output_template,
        write_subtitles=args.write_subs,
        write_auto_subtitles=args.write_auto_subs,
        subtitles_only=args.subtitles_only,
        subtitle_languages=args.sub_langs,
        overwrite=args.overwrite,
        write_info_json=args.write_info_json,
        download_archive=Path(args.download_archive) if args.download_archive else None,
        preset=args.preset,
        merge_format=args.merge_format,
        remux_video=args.remux_video,
        convert_subs=args.convert_subs,
        format_sort=args.format_sort,
        cookies=Path(args.cookies) if args.cookies else None,
        cookies_from_browser=args.cookies_from_browser,
        filename_template=None if args.output_template else args.filename_template,
        filename_language=args.filename_language,
        windows_filenames=args.windows_filenames,
    )
    options = make_fetch_options(urls, template)
    result = fetch_many(
        options, dry_run=args.dry_run, max_workers=args.max_workers, timeout=args.timeout
    )
    if args.summary_json:
        _write_json_file(Path(args.summary_json), result.to_dict())
    _print_fetch_summary(result.to_dict(), dry_run=args.dry_run)
    return 1 if result.failed else 0


def _fetch_urls_from_args(args: argparse.Namespace) -> list[str]:
    urls: list[str] = []
    if args.url:
        urls.append(args.url)
    if args.input_file:
        urls.extend(load_fetch_urls(args.input_file))
    if not urls:
        raise MediaToolsError("Provide a fetch URL or --input-file.")
    return urls


def _write_json_file(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _print_fetch_summary(payload: dict[str, object], *, dry_run: bool) -> None:
    action = "Planned" if dry_run else "Fetched"
    print(
        f"{action} {payload['total']} item(s): "
        f"{payload['succeeded']} succeeded, {payload['failed']} failed, "
        f"{payload['planned']} planned.",
    )
    for item in payload["items"]:
        assert isinstance(item, dict)
        print(f"- {item['status']}: {item['url']}")
        if dry_run:
            command = item.get("command", [])
            assert isinstance(command, list)
            print(f"  command: {' '.join(str(part) for part in command)}")
        if item.get("error"):
            print(f"  error: {item['error']}", file=sys.stderr)
