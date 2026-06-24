from __future__ import annotations

import subprocess

import pytest

from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch import (
    FetchOptions,
    build_fetch_args,
    fetch_media,
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
