from __future__ import annotations

import pytest

from mediatools.core.errors import MediaFileError
from mediatools.core.subtitle import convert_subtitle_file, convert_subtitle_text, parse_timestamp


def test_vtt_to_srt_strips_header_and_tags():
    vtt = """WEBVTT

00:00:01.000 --> 00:00:02.500 align:start
<v Speaker>Hello</v>
world
"""

    converted = convert_subtitle_text(vtt, source_format="vtt", target_format="srt")

    assert converted == "1\n00:00:01,000 --> 00:00:02,500\nHello\nworld\n"


def test_srt_to_vtt_renumbers_and_uses_dot_timestamps():
    srt = """9
00:00:01,000 --> 00:00:02,000
Hello

10
00:00:03,000 --> 00:00:04,000
Again
"""

    converted = convert_subtitle_text(srt, source_format="srt", target_format="vtt")

    assert converted.startswith("WEBVTT\n\n00:00:01.000 --> 00:00:02.000")
    assert "00:00:03.000 --> 00:00:04.000" in converted


def test_convert_subtitle_file_uses_extensions(tmp_path):
    source = tmp_path / "source.vtt"
    target = tmp_path / "target.srt"
    source.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHi\n", encoding="utf-8")

    output = convert_subtitle_file(source, target)

    assert output == target.resolve()
    assert target.read_text(encoding="utf-8") == "1\n00:00:01,000 --> 00:00:02,000\nHi\n"


def test_convert_subtitle_file_rejects_missing_input(tmp_path):
    with pytest.raises(MediaFileError, match="does not exist"):
        convert_subtitle_file(tmp_path / "missing.vtt", tmp_path / "target.srt")


def test_convert_subtitle_file_rejects_directory_input(tmp_path):
    with pytest.raises(MediaFileError, match="not a file"):
        convert_subtitle_file(tmp_path, tmp_path / "target.srt")


def test_parse_timestamp_accepts_comma_and_dot():
    assert parse_timestamp("00:00:01,250") == 1250
    assert parse_timestamp("00:00:01.250") == 1250
