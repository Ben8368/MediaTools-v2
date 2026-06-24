"""Command line entry point for MediaTools v2."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

from mediatools import __version__
from mediatools.core.encode import EncodeOptions, encode_media
from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch import fetch_many, load_fetch_urls, make_fetch_options
from mediatools.core.probe import format_probe_text, probe_media, summarize_probe
from mediatools.core.screenshot import ScreenshotOptions, capture_screenshot
from mediatools.core.subtitle import convert_subtitle_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mediatools",
        description="Cross-platform media tools.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show the MediaTools version and exit.",
    )

    subparsers = parser.add_subparsers(dest="command")
    doctor_parser = subparsers.add_parser("doctor", help="Check the local runtime environment.")
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the environment report as JSON.",
    )
    probe_parser = subparsers.add_parser("probe", help="Read media metadata with ffprobe.")
    probe_parser.add_argument("input", help="Media file to inspect.")
    probe_parser.add_argument("--json", action="store_true", help="Print metadata as JSON.")

    subtitle_parser = subparsers.add_parser("subtitle", help="Subtitle utilities.")
    subtitle_subparsers = subtitle_parser.add_subparsers(dest="subtitle_command")
    subtitle_convert = subtitle_subparsers.add_parser(
        "convert",
        help="Convert subtitles between SRT and WebVTT.",
    )
    subtitle_convert.add_argument("input", help="Input subtitle path.")
    subtitle_convert.add_argument("output", help="Output subtitle path.")
    subtitle_convert.add_argument("--from", dest="source_format", help="Input format: srt or vtt.")
    subtitle_convert.add_argument("--to", dest="target_format", help="Output format: srt or vtt.")
    subtitle_convert.add_argument(
        "--keep-tags",
        action="store_true",
        help="Keep inline subtitle tags instead of stripping them.",
    )

    encode_parser = subparsers.add_parser("encode", help="Transcode media or extract audio.")
    encode_parser.add_argument("input", help="Input media path.")
    encode_parser.add_argument("output", help="Output media path.")
    encode_parser.add_argument("--video-codec", help="ffmpeg video codec, e.g. libx265.")
    encode_parser.add_argument("--audio-codec", help="ffmpeg audio codec, e.g. aac.")
    encode_parser.add_argument("--video-bitrate", help="Video bitrate, e.g. 2M.")
    encode_parser.add_argument("--audio-bitrate", help="Audio bitrate, e.g. 192k.")
    encode_parser.add_argument(
        "--extract-audio",
        action="store_true",
        help="Drop video and write audio only.",
    )
    encode_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace output if it exists.",
    )

    screenshot_parser = subparsers.add_parser(
        "screenshot",
        help="Capture a video frame or extract frames by interval.",
    )
    screenshot_parser.add_argument("input", help="Input video path.")
    screenshot_parser.add_argument("output", help="Output image path or frame pattern.")
    screenshot_parser.add_argument(
        "--time",
        dest="timestamp",
        help="Timestamp in seconds or HH:MM:SS.",
    )
    screenshot_parser.add_argument(
        "--interval",
        type=float,
        help="Extract frames every N seconds. Output may be a directory or pattern.",
    )
    screenshot_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing outputs.",
    )

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
    return parser


def build_doctor_report() -> dict[str, object]:
    tools = {
        name: {"available": (path := shutil.which(name)) is not None, "path": path}
        for name in ("ffmpeg", "ffprobe", "yt-dlp")
    }
    return {
        "mediatools_version": __version__,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        **tools,
    }


def run_doctor(*, json_output: bool = False) -> int:
    report = build_doctor_report()
    if json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"MediaTools: {report['mediatools_version']}")
    print(f"Python: {report['python_version']}")
    print(f"Platform: {report['platform']}")
    for tool in ("ffmpeg", "ffprobe", "yt-dlp"):
        tool_info = report[tool]
        assert isinstance(tool_info, dict)
        status = "found" if tool_info["available"] else "missing"
        print(f"{tool}: {status}")
        if tool_info["path"]:
            print(f"{tool} path: {tool_info['path']}")
    return 0


def run_probe_command(args: argparse.Namespace) -> int:
    data = probe_media(args.input)
    summary = summarize_probe(data)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(format_probe_text(summary))
    return 0


def run_subtitle_command(args: argparse.Namespace) -> int:
    if args.subtitle_command != "convert":
        return 2
    output = convert_subtitle_file(
        args.input,
        args.output,
        source_format=args.source_format,
        target_format=args.target_format,
        clean_tags=not args.keep_tags,
    )
    print(f"Wrote {output}")
    return 0


def run_encode_command(args: argparse.Namespace) -> int:
    encode_media(
        EncodeOptions(
            input_path=Path(args.input),
            output_path=Path(args.output),
            video_codec=args.video_codec,
            audio_codec=args.audio_codec,
            video_bitrate=args.video_bitrate,
            audio_bitrate=args.audio_bitrate,
            extract_audio=args.extract_audio,
            overwrite=args.overwrite,
        ),
    )
    print(f"Wrote {Path(args.output).expanduser()}")
    return 0


def run_screenshot_command(args: argparse.Namespace) -> int:
    output_path = _screenshot_output_path(args.output, interval=args.interval)
    capture_screenshot(
        ScreenshotOptions(
            input_path=Path(args.input),
            output_path=output_path,
            timestamp=args.timestamp,
            interval_seconds=args.interval,
            overwrite=args.overwrite,
        ),
    )
    print(f"Wrote {output_path.expanduser()}")
    return 0


def run_fetch_command(args: argparse.Namespace) -> int:
    urls = _fetch_urls_from_args(args)
    options = make_fetch_options(
        urls,
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
    result = fetch_many(options, dry_run=args.dry_run)
    if args.summary_json:
        _write_json_file(Path(args.summary_json), result.to_dict())
    _print_fetch_summary(result.to_dict(), dry_run=args.dry_run)
    return 1 if result.failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.version:
            print(f"MediaTools {__version__}")
            return 0

        if args.command == "doctor":
            return run_doctor(json_output=args.json)
        if args.command == "probe":
            return run_probe_command(args)
        if args.command == "subtitle":
            return run_subtitle_command(args)
        if args.command == "encode":
            return run_encode_command(args)
        if args.command == "screenshot":
            return run_screenshot_command(args)
        if args.command == "fetch":
            return run_fetch_command(args)
    except MediaToolsError as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        return 1

    parser.print_help()
    return 0


def _screenshot_output_path(output: str, *, interval: float | None) -> Path:
    path = Path(output)
    if interval is None:
        return path
    if "%" in path.name:
        return path
    if path.suffix:
        return path
    return path / "frame_%04d.png"


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


if __name__ == "__main__":
    raise SystemExit(main())
