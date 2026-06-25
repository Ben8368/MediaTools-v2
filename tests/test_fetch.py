from __future__ import annotations

import subprocess

import pytest

from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch import (
    FetchOptions,
    fetch_many,
    fetch_media,
    load_fetch_urls,
    make_fetch_options,
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


def test_load_fetch_urls_rejects_directory(tmp_path):
    with pytest.raises(MediaToolsError, match="not a file"):
        load_fetch_urls(tmp_path)


def test_make_fetch_options_requires_urls(tmp_path):
    with pytest.raises(MediaToolsError):
        make_fetch_options([], FetchOptions(url="", output_dir=tmp_path))


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
    assert "AUTO-%(uploader)s-%(title).200B-%(extractor_key)s.%(ext)s" in result.items[0].command
    assert "--write-subs" in result.items[0].command
    assert "--write-info-json" in result.items[0].command
    assert "--windows-filenames" in result.items[0].command


def test_fetch_many_dry_run_keeps_original_without_language_probe(tmp_path, monkeypatch):
    def fail_probe(url, **kwargs):
        raise AssertionError("dry-run should not call yt-dlp for language probing")

    monkeypatch.setattr("mediatools.core.fetch.probe_language", fail_probe)

    result = fetch_many(
        [
            FetchOptions(
                url="https://example.com/video",
                output_dir=tmp_path,
                write_auto_subtitles=True,
                subtitle_languages="original",
                cookies_from_browser="safari",
            ),
        ],
        dry_run=True,
    )

    assert result.planned == 1
    assert "original" in result.items[0].command


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

    assert len(calls) == 4
    assert result.succeeded == 1
    assert result.failed == 1
    assert result.items[1].error == "network failed"


def test_fetch_many_records_keyboard_interrupt(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        raise KeyboardInterrupt

    result = fetch_many(
        [FetchOptions(url="https://example.com/video", output_dir=tmp_path)],
        runner=runner,
    )

    assert result.failed == 1
    assert "Interrupted by user" in str(result.items[0].error)


def test_fetch_media_only_postprocesses_changed_subtitles(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    old_subtitle = tmp_path / "old.en.srt"
    old_subtitle.write_text("OLD", encoding="utf-8")

    def runner(command, **kwargs):
        (tmp_path / "new.en.srt").write_text("NEW", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    fetch_media(FetchOptions(url="https://example.com/video", output_dir=tmp_path), runner=runner)

    assert old_subtitle.exists()
    assert not (tmp_path / "old.srt").exists()
    assert not (tmp_path / "new.en.srt").exists()
    assert (tmp_path / "new.srt").read_text(encoding="utf-8") == "NEW"


def test_make_fetch_options_accepts_new_fields(tmp_path):
    template = FetchOptions(
        url="",  # placeholder — replaced per-URL
        output_dir=tmp_path,
        preset="mp4",
        convert_subs="srt",
        format_sort="vcodec:h264",
        cookies=tmp_path / "cookies.txt",
        filename_template="{lang}-{title}.{ext}",
        filename_language="auto",
        windows_filenames=False,
    )
    opts = make_fetch_options(["https://example.com/video"], template)
    assert len(opts) == 1
    assert opts[0].preset == "mp4"
    assert opts[0].convert_subs == "srt"
    assert opts[0].format_sort == "vcodec:h264"
    assert opts[0].cookies == tmp_path / "cookies.txt"
    assert opts[0].filename_template == "{lang}-{title}.{ext}"
    assert opts[0].filename_language == "auto"
    assert opts[0].windows_filenames is False
