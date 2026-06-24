from __future__ import annotations

import subprocess

import pytest

from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch import (
    FetchOptions,
    _resolve_sub_langs,
    build_fetch_args,
    fetch_many,
    fetch_media,
    load_fetch_urls,
    make_fetch_options,
    probe_language,
    sanitize_output_template,
)


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
    assert "en,zh" in args


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


def test_sanitize_output_template_removes_cross_platform_trouble():
    assert (
        sanitize_output_template("bad:name\\with spaces.%(ext)s")
        == "bad_name/with_spaces.%(ext)s"
    )


def test_fetch_media_runs_ytdlp(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_media(
        FetchOptions(url="https://example.com/video", output_dir=tmp_path),
        runner=runner,
    )

    assert result.command[0] == "/bin/yt-dlp"
    assert "https://example.com/video" in result.command


def test_load_fetch_urls_ignores_blank_lines_and_comments(tmp_path):
    input_file = tmp_path / "urls.txt"
    input_file.write_text(
        "\n# comment\nhttps://example.com/one\n  https://example.com/two  \n",
        encoding="utf-8",
    )

    assert load_fetch_urls(input_file) == [
        "https://example.com/one",
        "https://example.com/two",
    ]


def test_load_fetch_urls_rejects_invalid_url(tmp_path):
    input_file = tmp_path / "urls.txt"
    input_file.write_text("ftp://example.com/video\n", encoding="utf-8")

    with pytest.raises(MediaToolsError):
        load_fetch_urls(input_file)


def test_make_fetch_options_requires_urls(tmp_path):
    with pytest.raises(MediaToolsError):
        make_fetch_options([], output_dir=tmp_path)


def test_fetch_many_dry_run_builds_plan_without_tool_lookup(tmp_path):
    result = fetch_many(
        [
            FetchOptions(
                url="https://example.com/video",
                output_dir=tmp_path,
                write_subtitles=True,
                subtitle_languages="en",
                write_info_json=True,
            ),
        ],
        dry_run=True,
    )

    assert result.total == 1
    assert result.planned == 1
    assert result.failed == 0
    assert result.items[0].command[0] == "yt-dlp"
    assert "--write-subs" in result.items[0].command
    assert "--write-info-json" in result.items[0].command


def test_fetch_many_collects_failures_and_continues(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        if "https://example.com/fail" in command:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="network failed")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [
            FetchOptions(url="https://example.com/ok", output_dir=tmp_path),
            FetchOptions(url="https://example.com/fail", output_dir=tmp_path),
        ],
        runner=runner,
    )

    assert len(calls) == 2
    assert result.succeeded == 1
    assert result.failed == 1
    assert result.items[1].error == "network failed"


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


def test_resolve_sub_langs_keeps_explicit_language(tmp_path):
    opts = FetchOptions(
        url="https://example.com/video",
        output_dir=tmp_path,
        subtitle_languages="en,ko",
    )
    resolved = _resolve_sub_langs(opts)
    assert resolved.subtitle_languages == "en,ko"


def test_resolve_sub_langs_uses_probed_language(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "mediatools.core.fetch.probe_language",
        lambda url, **kwargs: "en-US",
    )
    opts = FetchOptions(
        url="https://example.com/video",
        output_dir=tmp_path,
        subtitle_languages="original",
    )
    resolved = _resolve_sub_langs(opts)
    assert resolved.subtitle_languages == "en-US-orig,en-US,en-orig,en"


def test_resolve_sub_langs_base_only_language(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "mediatools.core.fetch.probe_language",
        lambda url, **kwargs: "ar",
    )
    opts = FetchOptions(
        url="https://example.com/video",
        output_dir=tmp_path,
        subtitle_languages="original",
    )
    resolved = _resolve_sub_langs(opts)
    assert resolved.subtitle_languages == "ar-orig,ar"
def test_resolve_sub_langs_falls_back_to_all_on_probe_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "mediatools.core.fetch.probe_language",
        lambda url, **kwargs: None,
    )
    opts = FetchOptions(
        url="https://example.com/video",
        output_dir=tmp_path,
        subtitle_languages="original",
    )
    resolved = _resolve_sub_langs(opts)
    assert resolved.subtitle_languages == "all"


def test_probe_language_returns_none_on_tool_error(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def failure_runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="network failed")

    result = probe_language("https://example.com/video", runner=failure_runner)
    assert result is None


def test_probe_language_returns_language_code(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="en-US\n", stderr="")

    result = probe_language("https://example.com/video", runner=runner)
    assert result == "en-US"


def test_make_fetch_options_accepts_new_fields(tmp_path):
    opts = make_fetch_options(
        ["https://example.com/video"],
        output_dir=tmp_path,
        preset="mp4",
        convert_subs="srt",
        format_sort="vcodec:h264",
    )
    assert len(opts) == 1
    assert opts[0].preset == "mp4"
    assert opts[0].convert_subs == "srt"
    assert opts[0].format_sort == "vcodec:h264"
