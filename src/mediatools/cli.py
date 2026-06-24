"""Command line entry point for MediaTools v2."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from collections.abc import Sequence

from mediatools import __version__


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
    return parser


def build_doctor_report() -> dict[str, object]:
    ffmpeg_path = shutil.which("ffmpeg")
    return {
        "mediatools_version": __version__,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "ffmpeg": {
            "available": ffmpeg_path is not None,
            "path": ffmpeg_path,
        },
    }


def run_doctor(*, json_output: bool = False) -> int:
    report = build_doctor_report()
    if json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    ffmpeg = report["ffmpeg"]
    assert isinstance(ffmpeg, dict)
    ffmpeg_status = "found" if ffmpeg["available"] else "missing"

    print(f"MediaTools: {report['mediatools_version']}")
    print(f"Python: {report['python_version']}")
    print(f"Platform: {report['platform']}")
    print(f"ffmpeg: {ffmpeg_status}")
    if ffmpeg["path"]:
        print(f"ffmpeg path: {ffmpeg['path']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"MediaTools {__version__}")
        return 0

    if args.command == "doctor":
        return run_doctor(json_output=args.json)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

