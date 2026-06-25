from __future__ import annotations

import pytest

from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch import FetchOptions, build_fetch_args


def test_build_fetch_args_for_subtitles_only(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            subtitles_only=True,
            subtitle_languages="en,zh",
        ),
    )

    assert "--skip-download" in args
    assert "--write-subs" in args
    assert "--write-auto-subs" in args
    assert "en,zh" in args
    assert "-t" not in args


def test_build_fetch_args_for_subtitles_only_respects_explicit_manual_choice(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            subtitles_only=True,
            write_subtitles=True,
            subtitle_languages="en",
        ),
    )

    assert "--skip-download" in args
    assert "--write-subs" in args
    assert "--write-auto-subs" not in args


def test_build_fetch_args_for_auto_subtitles(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            write_auto_subtitles=True,
            subtitle_languages="en",
        ),
    )

    assert "--write-auto-subs" in args
    assert "--sub-langs" in args
    assert "en" in args


def test_build_fetch_args_for_subs_and_auto_subs_deduplicates_sub_langs(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            write_subtitles=True,
            write_auto_subtitles=True,
            subtitle_languages="en,ko",
        ),
    )

    assert "--write-subs" in args
    assert "--write-auto-subs" in args
    assert args.count("--sub-langs") == 1
    assert args.count("en,ko") == 1


def test_build_fetch_args_for_info_json_and_archive(tmp_path):
    archive = tmp_path / "archive.txt"
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            write_info_json=True,
            download_archive=archive,
        ),
    )

    assert "--write-info-json" in args
    assert "--download-archive" in args
    assert str(archive) in args


def test_build_fetch_args_rejects_non_http_url(tmp_path):
    with pytest.raises(MediaToolsError):
        build_fetch_args(FetchOptions(url="file:///tmp/video", output_dir=tmp_path))


def test_build_fetch_args_with_preset(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            preset="mp4",
        ),
    )
    assert "-t" in args
    idx = args.index("-t")
    assert args[idx + 1] == "mp4"


def test_build_fetch_args_with_convert_subs(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            write_auto_subtitles=True,
            subtitle_languages="en",
            convert_subs="srt",
        ),
    )
    assert "--convert-subs" in args
    idx = args.index("--convert-subs")
    assert args[idx + 1] == "srt"


def test_build_fetch_args_with_merge_format_and_remux(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            merge_format="mp4",
            remux_video="mp4",
        ),
    )
    assert "--merge-output-format" in args
    assert "--remux-video" in args
    assert "mp4" in args


def test_build_fetch_args_with_format_sort(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            format_sort="vcodec:h264,res,fps",
        ),
    )
    assert "-S" in args
    idx = args.index("-S")
    assert args[idx + 1] == "vcodec:h264,res,fps"


def test_build_fetch_args_with_friendly_filename_template(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            filename_template="{lang}-{author}-{title}-{platform}.{ext}",
            filename_language="KR",
        ),
    )

    idx = args.index("--output")
    assert args[idx + 1] == "KR-%(uploader)s-%(title).200B-%(extractor_key)s.%(ext)s"
    assert "--windows-filenames" in args


def test_build_fetch_args_with_reordered_friendly_filename_template(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            filename_template="{platform}-{title}-{author}-{lang}.{ext}",
            filename_language="EN",
        ),
    )

    idx = args.index("--output")
    assert args[idx + 1] == "%(extractor_key)s-%(title).200B-%(uploader)s-EN.%(ext)s"


def test_build_fetch_args_allows_disabling_windows_filenames(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            windows_filenames=False,
        ),
    )

    assert "--windows-filenames" not in args


def test_build_fetch_args_with_cookies_file(tmp_path):
    cookies = tmp_path / "cookies.txt"
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            cookies=cookies,
        ),
    )
    assert "--cookies" in args
    idx = args.index("--cookies")
    assert args[idx + 1] == str(cookies)


def test_build_fetch_args_with_cookies_from_browser(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            cookies_from_browser="safari",
        ),
    )
    assert "--cookies-from-browser" in args
    idx = args.index("--cookies-from-browser")
    assert args[idx + 1] == "safari"


def test_build_fetch_args_rejects_multiple_cookie_sources(tmp_path):
    with pytest.raises(MediaToolsError):
        build_fetch_args(
            FetchOptions(
                url="https://example.com/video",
                output_dir=tmp_path,
                cookies=tmp_path / "cookies.txt",
                cookies_from_browser="safari",
            ),
        )
