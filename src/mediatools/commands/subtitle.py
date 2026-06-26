"""``mediatools subtitle`` — subtitle format conversion (SRT ↔ WebVTT)."""

from __future__ import annotations

import argparse
import sys

from mediatools.core.subtitle import convert_subtitle_file


def register_parser(subparsers: argparse._SubParsersAction) -> None:
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


def run(args: argparse.Namespace) -> int:
    if args.subtitle_command != "convert":
        print("Error: missing subcommand. Use: mediatools subtitle convert", file=sys.stderr)
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
