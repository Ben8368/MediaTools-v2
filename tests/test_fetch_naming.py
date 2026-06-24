from __future__ import annotations

import pytest

from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch_naming import (
    build_output_template,
    normalize_filename_language,
    render_filename_template,
    sanitize_output_template,
    template_uses_language,
    to_filename_language_code,
)


def test_render_filename_template_with_language_and_metadata_fields():
    template = render_filename_template(
        "{lang}-{author}-{title}-{platform}.{ext}",
        filename_language="kr",
    )

    assert template == "KR-%(uploader)s-%(title).200B-%(extractor_key)s.%(ext)s"


def test_build_output_template_defaults_to_language_author_title_platform():
    template = build_output_template(None)

    assert template == "AUTO-%(uploader)s-%(title).200B-%(extractor_key)s.%(ext)s"


def test_render_filename_template_appends_extension_when_missing():
    template = render_filename_template("{lang}-{title}", filename_language="EN")

    assert template == "EN-%(title).200B.%(ext)s"


def test_render_filename_template_keeps_literal_extension():
    template = render_filename_template("KR-{author}-{title}-{platform}.mp4")

    assert template == "KR-%(uploader)s-%(title).200B-%(extractor_key)s.mp4"


def test_render_filename_template_requires_language_for_lang_field():
    with pytest.raises(MediaToolsError, match="--name-language"):
        render_filename_template("{lang}-{title}.{ext}")


def test_render_filename_template_rejects_unknown_field():
    with pytest.raises(MediaToolsError, match="Unknown filename template field"):
        render_filename_template("{lang}-{series}.{ext}", filename_language="JP")


def test_build_output_template_prefers_friendly_template():
    template = build_output_template(
        None,
        filename_template="{lang}-{title}.{ext}",
        filename_language="PT",
    )

    assert template == "PT-%(title).200B.%(ext)s"


def test_build_output_template_raw_template_overrides_friendly_template():
    template = build_output_template(
        "%(id)s.%(ext)s",
        filename_template="{lang}-{title}.{ext}",
        filename_language="PT",
    )

    assert template == "%(id)s.%(ext)s"


def test_sanitize_output_template_still_supports_ytdlp_template():
    assert (
        sanitize_output_template("bad:name\\with spaces.%(ext)s")
        == "bad_name/with_spaces.%(ext)s"
    )


def test_template_uses_language_defaults_true():
    assert template_uses_language(None) is True
    assert template_uses_language("{author}-{title}.{ext}") is False


def test_to_filename_language_code_maps_common_codes():
    assert to_filename_language_code("ko") == "KR"
    assert to_filename_language_code("en-US") == "EN"
    assert to_filename_language_code("ja") == "JP"
    assert to_filename_language_code("zh-CN") == "SC"
    assert to_filename_language_code("zh-TW") == "TC"
    assert to_filename_language_code("ar") == "AR"
    assert to_filename_language_code("pt-BR") == "PT"


def test_to_filename_language_code_falls_back_to_upper_base():
    assert to_filename_language_code("tr-TR") == "TR"
    assert to_filename_language_code("NA") is None


def test_normalize_filename_language_allows_auto_placeholder():
    assert normalize_filename_language("auto") == "AUTO"


def test_strip_subtitle_language_suffix_removes_language_segment(tmp_path):
    """Verify that subtitle files get renamed to remove the language middle segment."""
    # Create a subtitle file with language suffix
    sub_file = tmp_path / "KR-Ben-Title-youtube.en.vtt"
    sub_file.write_text("WEBVTT")

    from mediatools.core.fetch_naming import strip_subtitle_language_suffix
    strip_subtitle_language_suffix(tmp_path)

    # The old file should be gone
    assert not sub_file.exists()
    # The new file should exist without the language segment
    renamed = tmp_path / "KR-Ben-Title-youtube.vtt"
    assert renamed.exists()
    assert renamed.read_text() == "WEBVTT"


def test_strip_subtitle_language_suffix_handles_multiple_langs(tmp_path):
    """When multiple subtitle languages exist, only the last (sorted) survives."""
    (tmp_path / "video.en.srt").write_text("EN")
    (tmp_path / "video.zh-Hans.srt").write_text("ZH")

    from mediatools.core.fetch_naming import strip_subtitle_language_suffix
    strip_subtitle_language_suffix(tmp_path)

    # The sorted-order last one (zh-Hans > en) should survive
    assert (tmp_path / "video.srt").exists()
    # Only the sorted-last file (zh-Hans > en) gets renamed; the earlier one stays.
    assert (tmp_path / "video.en.srt").exists()


def test_strip_subtitle_language_suffix_skips_video_files(tmp_path):
    """Video files without a language segment should be untouched."""
    (tmp_path / "KR-Ben-Title-youtube.mp4").write_text("bogus")
    (tmp_path / "KR-Ben-Title-youtube.en.vtt").write_text("WEBVTT")

    from mediatools.core.fetch_naming import strip_subtitle_language_suffix
    strip_subtitle_language_suffix(tmp_path)

    assert (tmp_path / "KR-Ben-Title-youtube.mp4").exists()
    # Only the vtt should have been renamed
    assert not (tmp_path / "KR-Ben-Title-youtube.en.vtt").exists()
    assert (tmp_path / "KR-Ben-Title-youtube.vtt").exists()


def test_strip_subtitle_language_suffix_empty_dir(tmp_path):
    """Empty directory should not raise."""
    from mediatools.core.fetch_naming import strip_subtitle_language_suffix
    strip_subtitle_language_suffix(tmp_path)  # no-op is fine
