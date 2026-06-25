"""Caption merging for sentence-aware subtitle grouping.

YouTube automatic captions often break sentences in the middle, producing
cues like ``"welcome back to the"`` followed by ``"channel. Today we're
diving into"``.  This module re-groups captions by sentence boundaries
while respecting temporal continuity and maximum duration/line constraints.

Supports multi-language sentence boundaries including:
- Western: . ! ?
- CJK (Chinese/Japanese/Korean): 。！？
- Arabic: ؟ ۔
- Devanagari (Hindi/etc): । ।।
"""

from __future__ import annotations

from mediatools.core.subtitle import Caption

# Sentence-ending punctuation across multiple writing systems
SENTENCE_ENDINGS = frozenset({
    ".", "!", "?",           # Western (Latin, Cyrillic, etc.)
    "。", "！", "？",        # CJK full-width
    "؟", "۔",               # Arabic question mark, Urdu full stop
    "।", "।।",              # Devanagari danda (single and double)
})


def merge_short_captions(
    captions: list[Caption],
    *,
    max_gap_ms: int = 200,
    max_duration_ms: int = 7000,
    max_lines: int = 2,
) -> list[Caption]:
    """Merge time-adjacent cues into natural sentence-length blocks.

    Args:
        captions: De-duplicated captions from ``clean_rolling_captions``.
        max_gap_ms: Maximum allowed gap between cues to still merge.
        max_duration_ms: Upper bound on merged cue duration before
            forcing a split.
        max_lines: Maximum number of text lines per merged cue.
    """
    if not captions:
        return []

    # Group by temporal continuity
    groups: list[list[Caption]] = []
    current_group: list[Caption] = [captions[0]]

    for caption in captions[1:]:
        prev = current_group[-1]
        gap = caption.start_ms - prev.end_ms

        if gap <= max_gap_ms:
            current_group.append(caption)
        else:
            groups.append(current_group)
            current_group = [caption]

    groups.append(current_group)

    # Split each group at sentence boundaries
    result: list[Caption] = []
    for group in groups:
        result.extend(_split_group_by_sentences(group, max_duration_ms, max_lines))

    return result


def _split_group_by_sentences(
    group: list[Caption],
    max_duration_ms: int,
    max_lines: int,
) -> list[Caption]:
    """Split a temporally-connected group of captions at sentence boundaries."""
    if len(group) == 1:
        return group

    all_words: list[tuple[int, int, str]] = []
    for cap in group:
        full_text = " ".join(cap.lines)
        words = full_text.split()
        if not words:
            continue
        dur = cap.end_ms - cap.start_ms
        per_word = dur / len(words) if words else 0
        for i, word in enumerate(words):
            w_start = int(cap.start_ms + i * per_word)
            w_end = int(cap.start_ms + (i + 1) * per_word)
            all_words.append((w_start, w_end, word))

    if not all_words:
        return group

    sentence_breaks: list[int] = []
    for i, (_, _, word) in enumerate(all_words):
        if word and word[-1] in SENTENCE_ENDINGS:
            sentence_breaks.append(i)

    if not sentence_breaks:
        # No sentence boundaries found — keep original captions unchanged.
        # Merging without sentence boundaries would produce arbitrary splits
        # that are worse than the original rolling fragments.
        return group

    results: list[Caption] = []
    word_start = 0
    for break_idx in sentence_breaks:
        sentence_words = all_words[word_start : break_idx + 1]
        if not sentence_words:
            word_start = break_idx + 1
            continue

        sent_start = sentence_words[0][0]
        sent_end = sentence_words[-1][1]
        sent_text = " ".join(w[2] for w in sentence_words)

        lines = _wrap_text(sent_text, max_lines)
        for line_group in _chunk_by_duration(
            sent_start, sent_end, lines, max_duration_ms
        ):
            results.append(
                Caption(
                    start_ms=line_group[0],
                    end_ms=line_group[1],
                    lines=line_group[2],
                ),
            )

        word_start = break_idx + 1

    if word_start < len(all_words):
        remaining = all_words[word_start:]
        rem_start = remaining[0][0]
        rem_end = remaining[-1][1]
        rem_text = " ".join(w[2] for w in remaining)
        lines = _wrap_text(rem_text, max_lines)
        for line_group in _chunk_by_duration(
            rem_start, rem_end, lines, max_duration_ms
        ):
            results.append(
                Caption(
                    start_ms=line_group[0],
                    end_ms=line_group[1],
                    lines=line_group[2],
                ),
            )

    return results if results else group


def _wrap_text(text: str, max_lines: int) -> list[str]:
    """Split text into at most max_lines lines at word boundaries."""
    words = text.split()
    if len(words) <= max_lines:
        return words

    words_per_line = len(words) / max_lines
    lines: list[str] = []
    for i in range(max_lines):
        start = int(i * words_per_line)
        end = int((i + 1) * words_per_line) if i < max_lines - 1 else len(words)
        lines.append(" ".join(words[start:end]))

    return lines


def _chunk_by_duration(
    start_ms: int,
    end_ms: int,
    lines: list[str],
    max_duration_ms: int,
) -> list[tuple[int, int, tuple[str, ...]]]:
    """Split lines into chunks that fit within max_duration_ms."""
    total_duration = end_ms - start_ms
    if total_duration <= max_duration_ms:
        return [(start_ms, end_ms, tuple(lines))]

    chunks: list[tuple[int, int, tuple[str, ...]]] = []
    chunk_dur = max_duration_ms
    num_chunks = (total_duration + chunk_dur - 1) // chunk_dur
    lines_per_chunk = max(len(lines) // num_chunks, 1)

    cursor = start_ms
    for i in range(0, len(lines), lines_per_chunk):
        chunk_lines = lines[i : i + lines_per_chunk]
        chunk_end = min(cursor + chunk_dur, end_ms)
        chunks.append((cursor, chunk_end, tuple(chunk_lines)))
        cursor = chunk_end

    # Ensure the last chunk extends to the original end_ms to prevent
    # truncation of subtitle display time
    if chunks and chunks[-1][1] < end_ms:
        last_start, _, last_lines = chunks[-1]
        chunks[-1] = (last_start, end_ms, last_lines)

    return chunks


def _group_by_duration(
    group: list[Caption],
    max_duration_ms: int,
    max_lines: int,
) -> list[Caption]:
    """Fallback: group captions by duration limit without sentence boundaries."""
    results: list[Caption] = []
    buffer: list[Caption] = [group[0]]

    for cap in group[1:]:
        total_dur = buffer[-1].end_ms - buffer[0].start_ms
        if total_dur + (cap.end_ms - cap.start_ms) <= max_duration_ms:
            buffer.append(cap)
        else:
            results.append(_merge_captions(buffer, max_lines))
            buffer = [cap]

    results.append(_merge_captions(buffer, max_lines))
    return results


def _merge_captions(caps: list[Caption], max_lines: int) -> Caption:
    """Merge a list of captions into one, wrapping text to max_lines."""
    if len(caps) == 1:
        return caps[0]

    all_text = " ".join(line for cap in caps for line in cap.lines)
    lines = _wrap_text(all_text, max_lines)
    return Caption(
        start_ms=caps[0].start_ms,
        end_ms=caps[-1].end_ms,
        lines=tuple(lines),
    )
