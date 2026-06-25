"""Command line entry point for MediaTools v2."""

from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Callable, Sequence

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
from mediatools.commands.serve import register_parser as register_serve
from mediatools.commands.serve import run as run_serve
from mediatools.commands.subtitle import register_parser as register_subtitle
from mediatools.commands.subtitle import run as run_subtitle
from mediatools.core.errors import MediaToolsError
from mediatools.core.logging import Logger, StreamHandler

CommandRunner = Callable[[argparse.Namespace], int]
COMMAND_RUNNERS: dict[str, CommandRunner] = {
    "doctor": run_doctor,
    "probe": run_probe,
    "subtitle": run_subtitle,
    "encode": run_encode,
    "screenshot": run_screenshot,
    "fetch": run_fetch,
    "serve": run_serve,
}


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

    # required=False intentionally: when no subcommand is given, we print help
    # and exit with code 0 (not an error).  This makes bare ``mediatools``
    # friendly for interactive users while still allowing scripts to check the
    # return code for success.
    subparsers = parser.add_subparsers(dest="command", required=False)
    register_doctor(subparsers)
    register_probe(subparsers)
    register_subtitle(subparsers)
    register_encode(subparsers)
    register_screenshot(subparsers)
    register_fetch(subparsers)
    register_serve(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logger = Logger(StreamHandler(stream=sys.stderr, show_level=False))

    try:
        if args.version:
            print(f"MediaTools {__version__}")
            return 0

        runner = COMMAND_RUNNERS.get(args.command)
        if runner is not None:
            return runner(args)
    except MediaToolsError as exc:
        logger.error(f"Error: {exc.message}")
        return 1
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}")
        traceback.print_exc(file=sys.stderr)
        return 2

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
