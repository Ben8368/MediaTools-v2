"""``mediatools encode`` — transcode media or extract audio via ffmpeg."""

from __future__ import annotations

import argparse
from pathlib import Path

from mediatools.core.encode import EncodeOptions, encode_media


def register_parser(subparsers: argparse._SubParsersAction) -> None:
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


def run(args: argparse.Namespace) -> int:
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
