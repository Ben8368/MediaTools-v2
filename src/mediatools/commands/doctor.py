"""``mediatools doctor`` — environment check and external tool discovery."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys

from mediatools import __version__


def build_doctor_report() -> dict[str, object]:
    """Build a structured environment report."""
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


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    doctor_parser = subparsers.add_parser("doctor", help="Check the local runtime environment.")
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the environment report as JSON.",
    )


def run(args: argparse.Namespace) -> int:
    report = build_doctor_report()
    if args.json:
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
