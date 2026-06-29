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


def _download_commands(commands: list[list[str]]) -> list[list[str]]:
    return [
        command
        for command in commands
        if "--print" not in command and "--dump-single-json" not in command
    ]


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


def test_fetch_many_records_changed_output_files(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        if "--print" not in command:
            (tmp_path / "video.mp4").write_bytes(b"media")
            (tmp_path / "video.en.srt").write_text("subtitle", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [FetchOptions(url="https://example.com/video", output_dir=tmp_path)],
        runner=runner,
    )

    assert result.succeeded == 1
    assert result.items[0].output_files == (tmp_path / "video.mp4", tmp_path / "video.srt")
    payload = result.to_dict()
    assert payload["items"][0]["output_files"] == [
        str(tmp_path / "video.mp4"),
        str(tmp_path / "video.srt"),
    ]


def test_fetch_many_downloads_video_before_best_effort_subtitles(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    commands: list[list[str]] = []

    def runner(command, **kwargs):
        commands.append(list(command))
        if "--print" in command:
            return subprocess.CompletedProcess(command, 0, stdout="zh-CN\n", stderr="")
        if "--skip-download" in command:
            return subprocess.CompletedProcess(
                command,
                1,
                stdout="",
                stderr="HTTP Error 429: Too Many Requests",
            )
        (tmp_path / "video.mp4").write_bytes(b"media")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [
            FetchOptions(
                url="https://example.com/video",
                output_dir=tmp_path,
                write_subtitles=True,
                write_auto_subtitles=True,
                subtitle_languages="original",
            ),
        ],
        runner=runner,
    )

    download_commands = _download_commands(commands)
    assert "--skip-download" not in download_commands[0]
    assert "--write-subs" not in download_commands[0]
    assert "--skip-download" in download_commands[1]
    assert result.succeeded == 1
    assert result.failed == 0
    assert result.items[0].output_files == (tmp_path / "video.mp4",)


def test_fetch_many_original_probe_failure_falls_back_to_orig_track(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    commands: list[list[str]] = []

    def runner(command, **kwargs):
        commands.append(list(command))
        if "--print" in command:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="language unavailable")
        if "--dump-single-json" in command:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        (tmp_path / "video.mp4").write_bytes(b"media")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [
            FetchOptions(
                url="https://example.com/video",
                output_dir=tmp_path,
                write_subtitles=True,
                write_auto_subtitles=True,
                subtitle_languages="original",
            ),
        ],
        runner=runner,
    )

    download_commands = _download_commands(commands)
    # Media downloads first (no subtitle flags), then a best-effort subtitle pass.
    assert len(download_commands) == 2
    assert "--write-subs" not in download_commands[0]
    subtitle_command = download_commands[1]
    assert "--sub-langs" in subtitle_command
    assert "^.*-orig$" in subtitle_command
    assert result.succeeded == 1
    assert result.items[0].output_files == (tmp_path / "video.mp4",)


def test_fetch_many_original_probe_uses_single_subtitle_language(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    commands: list[list[str]] = []

    def runner(command, **kwargs):
        commands.append(list(command))
        if "--print" in command:
            return subprocess.CompletedProcess(command, 0, stdout="NA\n", stderr="")
        if "--dump-single-json" in command:
            payload = '{"subtitles": {"zh-CN": [{"ext": "vtt"}]}, "automatic_captions": {}}'
            return subprocess.CompletedProcess(command, 0, stdout=payload, stderr="")
        if "--skip-download" in command:
            (tmp_path / "video.zh-CN.srt").write_text("subtitle", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        (tmp_path / "video.mp4").write_bytes(b"media")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [
            FetchOptions(
                url="https://example.com/video",
                output_dir=tmp_path,
                write_subtitles=True,
                write_auto_subtitles=True,
                subtitle_languages="original",
            ),
        ],
        runner=runner,
    )

    subtitle_command = _download_commands(commands)[1]
    subtitle_args = " ".join(subtitle_command)
    assert "^zh\\-CN$" in subtitle_args
    assert "^.*-orig$" not in subtitle_args
    assert result.succeeded == 1
    assert result.items[0].output_files == (tmp_path / "video.mp4", tmp_path / "video.srt")


def test_fetch_many_subtitles_only_original_probe_failure_uses_orig_track(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    commands: list[list[str]] = []

    def runner(command, **kwargs):
        commands.append(list(command))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [
            FetchOptions(
                url="https://example.com/video",
                output_dir=tmp_path,
                subtitles_only=True,
                subtitle_languages="original",
            ),
        ],
        runner=runner,
    )

    download_commands = _download_commands(commands)
    assert len(download_commands) == 1
    assert "--skip-download" in download_commands[0]
    assert "^.*-orig$" in download_commands[0]
    assert result.succeeded == 1


def test_fetch_many_translates_locked_cookie_error(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        if "--print" in command:
            return subprocess.CompletedProcess(command, 0, stdout="en\n", stderr="")
        return subprocess.CompletedProcess(
            command,
            1,
            stdout="",
            stderr="ERROR: Could not copy Chrome cookie database. See https://...",
        )

    result = fetch_many(
        [
            FetchOptions(
                url="https://example.com/video",
                output_dir=tmp_path,
                cookies_from_browser="chrome",
            ),
        ],
        runner=runner,
    )

    assert result.failed == 1
    error = str(result.items[0].error)
    assert "chrome" in error.lower()
    assert "退出" in error
    assert "不使用浏览器登录态" in error
    # Raw yt-dlp English text must be replaced, not appended.
    assert "Could not copy" not in error


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


def test_fetch_media_transcodes_only_changed_media(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    old_media = tmp_path / "old.mp4"
    old_media.write_bytes(b"old")
    transcode_paths: list[str] = []

    def runner(command, **kwargs):
        (tmp_path / "new.mp4").write_bytes(b"new")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    def fake_transcode_if_needed(path, options, *, runner=None):
        transcode_paths.append(path.name)
        return None

    monkeypatch.setattr(
        "mediatools.core.fetch.transcode_if_needed",
        fake_transcode_if_needed,
    )

    fetch_media(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            video_codec="h264",
        ),
        runner=runner,
    )

    assert old_media.exists()
    assert transcode_paths == ["new.mp4"]


def test_fetch_media_cleans_rolling_subtitle_text(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    rolling_srt = """1
00:00:00,000 --> 00:00:02,030
Picture this, you have an idea, a real

2
00:00:02,030 --> 00:00:02,040
Picture this, you have an idea, a real

3
00:00:02,040 --> 00:00:04,070
Picture this, you have an idea, a real
one, not a shower thought, a product
"""

    def runner(command, **kwargs):
        (tmp_path / "video.en.srt").write_text(rolling_srt, encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    fetch_media(FetchOptions(url="https://example.com/video", output_dir=tmp_path), runner=runner)

    cleaned = (tmp_path / "video.srt").read_text(encoding="utf-8")
    assert "Picture this, you have an idea, a real\n\n2" in cleaned
    assert "Picture this, you have an idea, a real\none, not" not in cleaned
    assert "one, not a shower thought, a product" in cleaned


def test_fetch_media_prefers_original_subtitle_over_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        (tmp_path / "video.en-orig.srt").write_text("ORIGINAL", encoding="utf-8")
        (tmp_path / "video.en.srt").write_text("FALLBACK", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    fetch_media(
        FetchOptions(url="https://example.com/video", output_dir=tmp_path),
        runner=runner,
        prefer_original_subtitles=True,
    )

    assert not (tmp_path / "video.en-orig.srt").exists()
    assert not (tmp_path / "video.en.srt").exists()
    assert (tmp_path / "video.srt").read_text(encoding="utf-8") == "ORIGINAL"


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
