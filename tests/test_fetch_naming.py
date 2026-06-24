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
