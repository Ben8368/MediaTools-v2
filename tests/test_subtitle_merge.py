"""Tests for subtitle merging and chunking behavior."""

from __future__ import annotations

from mediatools.core.subtitle import Caption
from mediatools.core.subtitle_merge import SENTENCE_ENDINGS, merge_short_captions


def test_merge_preserves_original_duration_when_split():
    """Long sentence merged with max_duration constraint must preserve original end_ms."""
    # 15-second single caption, max_duration=7 seconds, max_lines=2
    caption = Caption(
        start_ms=0,
        end_ms=15000,
        lines=("This is a long sentence that will be wrapped.",),
    )
    result = merge_short_captions([caption], max_duration_ms=7000, max_lines=2)

    assert result, "Should return at least one caption"
    assert result[-1].end_ms == 15000, (
        f"Last caption must end at 15000ms to preserve original duration, "
        f"got {result[-1].end_ms}ms (lost {15000 - result[-1].end_ms}ms)"
    )


def test_merge_short_captions_handles_single_line_long_duration():
    """Single-line caption with duration exceeding max_duration must not be truncated."""
    caption = Caption(start_ms=0, end_ms=10000, lines=("One line text.",))
    result = merge_short_captions([caption], max_duration_ms=5000, max_lines=2)

    assert result
    assert result[-1].end_ms == 10000, "Single line split must preserve original end time"


def test_merge_multiple_captions_preserves_last_end_time():
    """Multiple captions merged into sentences must preserve the final end_ms."""
    captions = [
        Caption(start_ms=0, end_ms=2000, lines=("Hello",)),
        Caption(start_ms=2000, end_ms=4000, lines=("world.",)),
        Caption(start_ms=4100, end_ms=6000, lines=("How are",)),
        Caption(start_ms=6000, end_ms=8500, lines=("you?",)),
    ]
    result = merge_short_captions(captions, max_duration_ms=5000, max_lines=2)

    assert result
    # The last merged caption should end at the original last caption's end_ms
    assert result[-1].end_ms == 8500, "Final merged caption must preserve original end time"


def test_merge_respects_sentence_boundaries():
    """Captions should be split at sentence boundaries when possible."""
    captions = [
        Caption(start_ms=0, end_ms=2000, lines=("First sentence.",)),
        Caption(start_ms=2000, end_ms=4000, lines=("Second sentence.",)),
    ]
    result = merge_short_captions(captions, max_duration_ms=7000, max_lines=2)

    # Should produce at least 2 captions (one per sentence)
    assert len(result) >= 2, "Sentence boundaries should be preserved"
    # First caption should end after first sentence
    assert "First sentence." in " ".join(result[0].lines)


def test_sentence_endings_includes_multilingual_punctuation():
    """SENTENCE_ENDINGS constant must include multi-language punctuation."""
    # Western
    assert "." in SENTENCE_ENDINGS
    assert "!" in SENTENCE_ENDINGS
    assert "?" in SENTENCE_ENDINGS

    # CJK full-width
    assert "。" in SENTENCE_ENDINGS
    assert "！" in SENTENCE_ENDINGS
    assert "？" in SENTENCE_ENDINGS

    # Arabic
    assert "؟" in SENTENCE_ENDINGS
    assert "۔" in SENTENCE_ENDINGS

    # Devanagari
    assert "।" in SENTENCE_ENDINGS
    assert "।।" in SENTENCE_ENDINGS


def test_merge_recognizes_cjk_sentence_boundaries():
    """Merging must recognize CJK full-width punctuation as sentence boundaries."""
    captions = [
        Caption(start_ms=0, end_ms=2000, lines=("你好世界。",)),
        Caption(start_ms=2000, end_ms=4000, lines=("今天天气很好。",)),
    ]
    result = merge_short_captions(captions, max_duration_ms=7000, max_lines=2)

    # Should produce at least 2 captions (one per CJK sentence)
    assert len(result) >= 2, "CJK sentence boundaries should be preserved"


def test_merge_recognizes_arabic_question_mark():
    """Merging must recognize Arabic question mark as sentence boundary."""
    captions = [
        Caption(start_ms=0, end_ms=2000, lines=("كيف حالك؟",)),
        Caption(start_ms=2000, end_ms=4000, lines=("أنا بخير۔",)),
    ]
    result = merge_short_captions(captions, max_duration_ms=7000, max_lines=2)

    # Should produce at least 2 captions (one per Arabic sentence)
    assert len(result) >= 2, "Arabic sentence boundaries should be preserved"

