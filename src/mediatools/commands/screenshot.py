"""``mediatools screenshot`` — capture video frames via ffmpeg."""

from __future__ import annotations

import argparse
from pathlib import Path

from mediatools.core.screenshot import ScreenshotOptions, capture_screenshot


def register_parser(subparsers: argparse._SubParsersAction) -> None:
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


def run(args: argparse.Namespace) -> int:
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


def _screenshot_output_path(output: str, *, interval: float | None) -> Path:
    path = Path(output)
    if interval is None:
        return path
    if "%" in path.name:
        return path
    if path.suffix:
        return path
    return path / "frame_%04d.png"
