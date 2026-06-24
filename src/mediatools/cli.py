"""Command line entry point for MediaTools v2."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from mediatools import __version__
from mediatools.commands.doctor import build_doctor_report  # noqa: F401  # re-exported
from mediatools.commands.doctor import register_parser as register_doctor
from mediatools.commands.doctor import run as run_doctor
from mediatools.commands.encode import register_parser as register_encode
from mediatools.commands.encode import run as run_encode
from mediatools.commands.fetch import register_parser as register_fetch
from mediatools.commands.fetch import run as run_fetch
from mediatools.commands.probe import register_parser as register_probe
from mediatools.commands.probe import run as run_probe
from mediatools.commands.screenshot import register_parser as register_screenshot
from mediatools.commands.screenshot import run as run_screenshot
from mediatools.commands.subtitle import register_parser as register_subtitle
from mediatools.commands.subtitle import run as run_subtitle
from mediatools.core.errors import MediaToolsError


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
    register_doctor(subparsers)
    register_probe(subparsers)
    register_subtitle(subparsers)
    register_encode(subparsers)
    register_screenshot(subparsers)
    register_fetch(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.version:
            print(f"MediaTools {__version__}")
            return 0

        if args.command == "doctor":
            return run_doctor(args)
        if args.command == "probe":
            return run_probe(args)
        if args.command == "subtitle":
            return run_subtitle(args)
        if args.command == "encode":
            return run_encode(args)
        if args.command == "screenshot":
            return run_screenshot(args)
        if args.command == "fetch":
            return run_fetch(args)
    except MediaToolsError as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
