"""Media metadata probing via ffprobe."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from mediatools.core.errors import MediaFileError, MediaToolsError
from mediatools.core.ffmpeg import ProcessRunner, run_ffprobe
from mediatools.core.paths import normalize


def build_probe_args(input_path: str | Path) -> list[str]:
    """Build ffprobe arguments for structured metadata output."""
    path = normalize(input_path)
    return [
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]


def probe_media(
    input_path: str | Path,
    *,
    runner: ProcessRunner | None = None,
) -> dict[str, object]:
    """Probe a media file and return parsed ffprobe JSON."""
    path = normalize(input_path)
    if not path.exists():
        raise MediaFileError("Input media file does not exist.", path=str(path))
    if not path.is_file():
        raise MediaFileError("Input path is not a file.", path=str(path))

    kwargs = {"runner": runner} if runner is not None else {}
    result = run_ffprobe(build_probe_args(path), **kwargs)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise MediaToolsError(
            "ffprobe returned invalid JSON.",
            details={"path": str(path), "stdout": result.stdout},
        ) from exc

    if not isinstance(data, dict):
        raise MediaToolsError("ffprobe returned an unexpected JSON payload.")
    return data


def summarize_probe(data: dict[str, object]) -> dict[str, object]:
    """Extract the high-value fields used by text and JSON CLI output."""
    streams = _as_list(data.get("streams"))
    format_info = _as_dict(data.get("format"))
    video_stream = _first_stream(streams, "video")
    audio_stream = _first_stream(streams, "audio")

    summary: dict[str, object] = {
        "duration": format_info.get("duration"),
        "format_name": format_info.get("format_name"),
        "bit_rate": format_info.get("bit_rate"),
        "size": format_info.get("size"),
        "stream_count": len(streams),
        "video": _stream_summary(video_stream, fields=("codec_name", "width", "height")),
        "audio": _stream_summary(audio_stream, fields=("codec_name", "sample_rate", "channels")),
        "streams": streams,
    }
    return summary


def format_probe_text(summary: dict[str, object]) -> str:
    """Format a compact human-readable probe report."""
    lines = [
        f"Duration: {_value(summary.get('duration'))}",
        f"Format: {_value(summary.get('format_name'))}",
        f"Bitrate: {_value(summary.get('bit_rate'))}",
        f"Streams: {_value(summary.get('stream_count'))}",
    ]

    video = _as_dict(summary.get("video"))
    if video:
        lines.append(
            "Video: "
            f"{_value(video.get('codec_name'))} "
            f"{_value(video.get('width'))}x{_value(video.get('height'))}",
        )

    audio = _as_dict(summary.get("audio"))
    if audio:
        lines.append(
            "Audio: "
            f"{_value(audio.get('codec_name'))} "
            f"{_value(audio.get('sample_rate'))}Hz "
            f"{_value(audio.get('channels'))}ch",
        )
    return "\n".join(lines)


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _first_stream(streams: Sequence[object], codec_type: str) -> dict[str, object]:
    for stream in streams:
        stream_dict = _as_dict(stream)
        if stream_dict.get("codec_type") == codec_type:
            return stream_dict
    return {}


def _stream_summary(stream: dict[str, object], *, fields: Sequence[str]) -> dict[str, object]:
    return {field: stream[field] for field in fields if field in stream}


def _value(value: object) -> str:
    if value is None:
        return "unknown"
    return str(value)
