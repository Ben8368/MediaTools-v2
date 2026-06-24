"""ffmpeg-based transcoding and audio extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mediatools.core.errors import MediaFileError
from mediatools.core.ffmpeg import ProcessRunner, ToolResult, run_ffmpeg
from mediatools.core.paths import normalize


@dataclass(frozen=True)
class EncodeOptions:
    """Options for a single encode operation."""

    input_path: Path
    output_path: Path
    video_codec: str | None = None
    audio_codec: str | None = None
    video_bitrate: str | None = None
    audio_bitrate: str | None = None
    extract_audio: bool = False
    overwrite: bool = False


def build_encode_args(options: EncodeOptions) -> list[str]:
    """Build ffmpeg arguments for transcoding or audio extraction."""
    args = ["-y" if options.overwrite else "-n", "-i", str(normalize(options.input_path))]

    if options.extract_audio:
        args.append("-vn")
        args.extend(["-c:a", options.audio_codec or _default_audio_codec(options.output_path)])
    else:
        if options.video_codec:
            args.extend(["-c:v", options.video_codec])
        if options.audio_codec:
            args.extend(["-c:a", options.audio_codec])

    if options.video_bitrate and not options.extract_audio:
        args.extend(["-b:v", options.video_bitrate])
    if options.audio_bitrate:
        args.extend(["-b:a", options.audio_bitrate])

    args.append(str(normalize(options.output_path)))
    return args


def encode_media(
    options: EncodeOptions,
    *,
    runner: ProcessRunner | None = None,
    timeout: float | None = None,
) -> ToolResult:
    """Run ffmpeg for a single encode operation."""
    input_path = normalize(options.input_path)
    output_path = normalize(options.output_path)
    _validate_input_file(input_path)
    _prepare_output_path(output_path, overwrite=options.overwrite)

    normalized_options = EncodeOptions(
        input_path=input_path,
        output_path=output_path,
        video_codec=options.video_codec,
        audio_codec=options.audio_codec,
        video_bitrate=options.video_bitrate,
        audio_bitrate=options.audio_bitrate,
        extract_audio=options.extract_audio,
        overwrite=options.overwrite,
    )
    kwargs = {"runner": runner} if runner is not None else {}
    return run_ffmpeg(build_encode_args(normalized_options), timeout=timeout, **kwargs)


def _validate_input_file(path: Path) -> None:
    if not path.exists():
        raise MediaFileError("Input media file does not exist.", path=str(path))
    if not path.is_file():
        raise MediaFileError("Input path is not a file.", path=str(path))


def _prepare_output_path(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise MediaFileError(
            "Output file already exists. Use --overwrite to replace it.",
            path=str(path),
        )
    path.parent.mkdir(parents=True, exist_ok=True)


def _default_audio_codec(output_path: Path) -> str:
    suffix = output_path.suffix.lower()
    if suffix == ".mp3":
        return "libmp3lame"
    if suffix in {".m4a", ".aac"}:
        return "aac"
    if suffix == ".flac":
        return "flac"
    return "copy"
