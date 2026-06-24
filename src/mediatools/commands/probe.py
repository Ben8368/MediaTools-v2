"""``mediatools probe`` — read media metadata via ffprobe."""

from __future__ import annotations

import argparse
import json

from mediatools.core.probe import format_probe_text, probe_media, summarize_probe


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    probe_parser = subparsers.add_parser("probe", help="Read media metadata with ffprobe.")
    probe_parser.add_argument("input", help="Media file to inspect.")
    probe_parser.add_argument("--json", action="store_true", help="Print metadata as JSON.")


def run(args: argparse.Namespace) -> int:
    data = probe_media(args.input)
    summary = summarize_probe(data)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(format_probe_text(summary))
    return 0
