"""Subtitle parsing and conversion helpers for SRT and WebVTT."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from mediatools.core.errors import MediaToolsError
from mediatools.core.paths import normalize

TIME_LINE_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{3})(?P<settings>.*)",
)
TAG_RE = re.compile(r"</?[^>]+>")


@dataclass(frozen=True)
class Caption:
    """A normalized subtitle cue."""

    start_ms: int
    end_ms: int
    lines: tuple[str, ...]


def convert_subtitle_text(
    text: str,
    *,
    source_format: str,
    target_format: str,
    clean_tags: bool = True,
) -> str:
    """Convert subtitle text between ``srt`` and ``vtt``."""
    source = _normalize_format(source_format)
    target = _normalize_format(target_format)
    captions = parse_subtitle(text, subtitle_format=source, clean_tags=clean_tags)

    if target == "srt":
        return serialize_srt(captions)
    if target == "vtt":
        return serialize_vtt(captions)
    raise MediaToolsError(f"Unsupported target subtitle format: {target_format}")


def convert_subtitle_file(
    input_path: str | Path,
    output_path: str | Path,
    *,
    source_format: str | None = None,
    target_format: str | None = None,
    clean_tags: bool = True,
) -> Path:
    """Convert a subtitle file and write the result with UTF-8 encoding."""
    input_file = normalize(input_path)
    output_file = normalize(output_path)
    source = source_format or input_file.suffix.lstrip(".")
    target = target_format or output_file.suffix.lstrip(".")

    text = input_file.read_text(encoding="utf-8-sig")
    converted = convert_subtitle_text(
        text,
        source_format=source,
        target_format=target,
        clean_tags=clean_tags,
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(converted, encoding="utf-8", newline="\n")
    return output_file


def parse_subtitle(
    text: str,
    *,
    subtitle_format: str,
    clean_tags: bool = True,
) -> list[Caption]:
    """Parse SRT or WebVTT text into normalized captions."""
    fmt = _normalize_format(subtitle_format)
    normalized = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    if fmt == "srt":
        return _parse_srt(normalized, clean_tags=clean_tags)
    if fmt == "vtt":
        return _parse_vtt(normalized, clean_tags=clean_tags)
    raise MediaToolsError(f"Unsupported source subtitle format: {subtitle_format}")


def serialize_srt(captions: list[Caption]) -> str:
    """Serialize captions as SRT with 1-based cue numbering."""
    blocks = []
    for index, caption in enumerate(captions, start=1):
        block = [
            str(index),
            f"{format_timestamp(caption.start_ms, comma=True)} --> "
            f"{format_timestamp(caption.end_ms, comma=True)}",
            *caption.lines,
        ]
        blocks.append("\n".join(block))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def serialize_vtt(captions: list[Caption]) -> str:
    """Serialize captions as WebVTT."""
    blocks = ["WEBVTT"]
    for caption in captions:
        block = [
            f"{format_timestamp(caption.start_ms, comma=False)} --> "
            f"{format_timestamp(caption.end_ms, comma=False)}",
            *caption.lines,
        ]
        blocks.append("\n".join(block))
    return "\n\n".join(blocks) + "\n"


def parse_timestamp(value: str) -> int:
    """Parse ``HH:MM:SS.mmm`` or ``HH:MM:SS,mmm`` into milliseconds."""
    main, milliseconds = value.replace(",", ".").split(".", maxsplit=1)
    hours, minutes, seconds = [int(part) for part in main.split(":")]
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + int(milliseconds[:3])


def format_timestamp(milliseconds: int, *, comma: bool) -> str:
    """Format milliseconds as a subtitle timestamp."""
    separator = "," if comma else "."
    total_seconds, ms = divmod(milliseconds, 1000)
    minutes_total, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes_total, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}{separator}{ms:03}"


def _parse_srt(text: str, *, clean_tags: bool) -> list[Caption]:
    captions: list[Caption] = []
    for block in _split_blocks(text):
        lines = block.split("\n")
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        captions.extend(_caption_from_lines(lines, clean_tags=clean_tags))
    return captions


def _parse_vtt(text: str, *, clean_tags: bool) -> list[Caption]:
    lines = text.split("\n")
    if lines and lines[0].lstrip("\ufeff").strip().startswith("WEBVTT"):
        lines = lines[1:]

    captions: list[Caption] = []
    current: list[str] = []
    skip_note = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("NOTE", "STYLE", "REGION")):
            skip_note = True
            continue
        if skip_note and stripped:
            continue
        if skip_note and not stripped:
            skip_note = False
            continue
        current.append(line)
    for block in _split_blocks("\n".join(current)):
        captions.extend(_caption_from_lines(block.split("\n"), clean_tags=clean_tags))
    return captions


def _caption_from_lines(lines: list[str], *, clean_tags: bool) -> list[Caption]:
    if not lines:
        return []
    time_index = next((index for index, line in enumerate(lines) if "-->" in line), None)
    if time_index is None:
        return []

    match = TIME_LINE_RE.search(lines[time_index].strip())
    if match is None:
        raise MediaToolsError(f"Invalid subtitle time range: {lines[time_index]}")

    payload = [_clean_line(line, clean_tags=clean_tags) for line in lines[time_index + 1 :]]
    payload = [line for line in payload if line]
    return [
        Caption(
            start_ms=parse_timestamp(match.group("start")),
            end_ms=parse_timestamp(match.group("end")),
            lines=tuple(payload),
        ),
    ]


def _split_blocks(text: str) -> list[str]:
    return [block.strip("\n") for block in re.split(r"\n{2,}", text.strip()) if block.strip()]


def _clean_line(line: str, *, clean_tags: bool) -> str:
    cleaned = line.strip()
    if clean_tags:
        cleaned = TAG_RE.sub("", cleaned)
    return cleaned


def _normalize_format(value: str) -> str:
    normalized = value.lower().lstrip(".")
    if normalized == "webvtt":
        return "vtt"
    if normalized in {"srt", "vtt"}:
        return normalized
    raise MediaToolsError(f"Unsupported subtitle format: {value}")
