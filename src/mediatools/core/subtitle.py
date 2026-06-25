"""Subtitle parsing and conversion helpers for SRT and WebVTT."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from mediatools.core.errors import MediaFileError, MediaToolsError
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
    clean_rolling: bool = True,
) -> str:
    """Convert subtitle text between ``srt`` and ``vtt``."""
    source = _normalize_format(source_format)
    target = _normalize_format(target_format)
    captions = parse_subtitle(text, subtitle_format=source, clean_tags=clean_tags)
    if clean_rolling:
        captions = clean_rolling_captions(captions)
        captions = merge_short_captions(captions)

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
    clean_rolling: bool = True,
) -> Path:
    """Convert a subtitle file and write the result with UTF-8 encoding."""
    input_file = normalize(input_path)
    output_file = normalize(output_path)
    source = source_format or input_file.suffix.lstrip(".")
    target = target_format or output_file.suffix.lstrip(".")

    if not input_file.exists():
        raise MediaFileError("Input subtitle file does not exist.", path=str(input_file))
    if not input_file.is_file():
        raise MediaFileError("Input subtitle path is not a file.", path=str(input_file))

    try:
        text = input_file.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise MediaFileError(
            "Could not read input subtitle file.",
            path=str(input_file),
        ) from exc
    converted = convert_subtitle_text(
        text,
        source_format=source,
        target_format=target,
        clean_tags=clean_tags,
        clean_rolling=clean_rolling,
    )
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(converted, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise MediaFileError(
            "Could not write output subtitle file.",
            path=str(output_file),
        ) from exc
    return output_file


def clean_subtitle_file(path: str | Path) -> Path:
    """Rewrite an SRT or WebVTT file after removing rolling duplicate text."""
    subtitle_file = normalize(path)
    subtitle_format = subtitle_file.suffix.lstrip(".").lower()
    if subtitle_format not in {"srt", "vtt"}:
        return subtitle_file
    if not subtitle_file.exists() or not subtitle_file.is_file():
        return subtitle_file
    try:
        text = subtitle_file.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise MediaFileError(
            "Could not read subtitle file for cleanup.",
            path=str(subtitle_file),
        ) from exc
    captions = parse_subtitle(text, subtitle_format=subtitle_format, clean_tags=True)
    if not captions:
        return subtitle_file
    captions = clean_rolling_captions(captions)
    captions = merge_short_captions(captions)
    cleaned = serialize_srt(captions) if subtitle_format == "srt" else serialize_vtt(captions)
    try:
        subtitle_file.write_text(cleaned, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise MediaFileError(
            "Could not write cleaned subtitle file.",
            path=str(subtitle_file),
        ) from exc
    return subtitle_file


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


def clean_rolling_captions(captions: list[Caption]) -> list[Caption]:
    """Remove repeated rolling subtitle prefixes from consecutive cues."""
    cleaned: list[Caption] = []
    previous_lines: tuple[str, ...] = ()
    for caption in captions:
        lines = _remove_line_overlap(previous_lines, caption.lines)
        if lines:
            cleaned.append(
                Caption(
                    start_ms=caption.start_ms,
                    end_ms=caption.end_ms,
                    lines=lines,
                ),
            )
        previous_lines = caption.lines
    return cleaned


def merge_short_captions(captions: list[Caption], **kwargs: object) -> list[Caption]:
    """Merge time-adjacent cues into natural sentence-length blocks.

    Delegated to ``subtitle_merge`` module to keep this file under 500 lines.
    """
    from mediatools.core.subtitle_merge import merge_short_captions as _merge

    return _merge(captions, **kwargs)  # type: ignore[arg-type]


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
        if skip_note:
            if "-->" in stripped:
                skip_note = False
            elif not stripped:
                skip_note = False
                continue
            else:
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


def _remove_line_overlap(
    previous_lines: tuple[str, ...],
    current_lines: tuple[str, ...],
) -> tuple[str, ...]:
    if not previous_lines or not current_lines:
        return current_lines
    limit = min(len(previous_lines), len(current_lines))
    for overlap in range(limit, 0, -1):
        if previous_lines[-overlap:] == current_lines[:overlap]:
            return current_lines[overlap:]
    return current_lines


def _normalize_format(value: str) -> str:
    normalized = value.lower().lstrip(".")
    if normalized == "webvtt":
        return "vtt"
    if normalized in {"srt", "vtt"}:
        return normalized
    raise MediaToolsError(f"Unsupported subtitle format: {value}")
