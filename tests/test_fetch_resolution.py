from __future__ import annotations

import subprocess

from mediatools.core.fetch import (
    FetchOptions,
    _resolve_filename_language,
    _resolve_sub_langs,
    probe_language,
    probe_original_subtitle_language,
)


def test_resolve_sub_langs_keeps_explicit_language(tmp_path):
    opts = FetchOptions(
        url="https://example.com/video",
        output_dir=tmp_path,
        subtitle_languages="en,ko",
    )
    resolved = _resolve_sub_langs(opts, probed_lang=None)
    assert resolved.subtitle_languages == "en,ko"


def test_resolve_sub_langs_uses_probed_language(tmp_path):
    opts = FetchOptions(
        url="https://example.com/video",
        output_dir=tmp_path,
        subtitle_languages="original",
    )
    resolved = _resolve_sub_langs(opts, probed_lang="en-US")
    assert resolved.subtitle_languages == "^en\\-US\\-orig$,^en\\-US$,^en\\-orig$,^en$"


def test_resolve_sub_langs_anchors_locale_to_avoid_translated_subtitles(tmp_path):
    opts = FetchOptions(
        url="https://example.com/video",
        output_dir=tmp_path,
        subtitle_languages="original",
    )
    resolved = _resolve_sub_langs(opts, probed_lang="zh-CN")

    assert resolved.subtitle_languages == "^zh\\-CN\\-orig$,^zh\\-CN$,^zh\\-orig$,^zh$"
    assert "zh-CN" not in resolved.subtitle_languages.split(",")


def test_resolve_sub_langs_base_only_language(tmp_path):
    opts = FetchOptions(
        url="https://example.com/video",
        output_dir=tmp_path,
        subtitle_languages="original",
    )
    resolved = _resolve_sub_langs(opts, probed_lang="ar")
    assert resolved.subtitle_languages == "^ar\\-orig$,^ar$"


def test_resolve_sub_langs_falls_back_to_original_track_on_probe_failure(tmp_path):
    opts = FetchOptions(
        url="https://example.com/video",
        output_dir=tmp_path,
        write_subtitles=True,
        write_auto_subtitles=True,
        subtitle_languages="original",
    )
    resolved = _resolve_sub_langs(opts, probed_lang=None)
    assert resolved.subtitle_languages == "^.*-orig$"
    assert resolved.write_subtitles is True
    assert resolved.write_auto_subtitles is True


def test_resolve_filename_language_uses_probed_language(tmp_path):
    opts = FetchOptions(url="https://example.com/video", output_dir=tmp_path)

    resolved = _resolve_filename_language(opts, probed_lang="zh-TW")

    assert resolved.filename_language == "TC"


def test_resolve_filename_language_falls_back_to_unknown(tmp_path):
    opts = FetchOptions(url="https://example.com/video", output_dir=tmp_path)

    resolved = _resolve_filename_language(opts, probed_lang=None)

    assert resolved.filename_language == "UN"


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


def test_probe_language_returns_first_language_for_playlist(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="zh-CN\nzh-TW\n", stderr="")

    result = probe_language("https://example.com/playlist", runner=runner)
    assert result == "zh-CN"


def test_probe_language_passes_cookie_source(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="zh-CN\n", stderr="")

    result = probe_language(
        "https://example.com/video",
        cookies_from_browser="safari",
        runner=runner,
    )
    assert result == "zh-CN"
    assert "--cookies-from-browser" in commands[0]
    assert "safari" in commands[0]


def test_probe_original_subtitle_language_uses_single_manual_subtitle(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        payload = '{"subtitles": {"zh-CN": [{"ext": "vtt"}]}, "automatic_captions": {}}'
        return subprocess.CompletedProcess(command, 0, stdout=payload, stderr="")

    result = probe_original_subtitle_language("https://example.com/video", runner=runner)

    assert result == "zh-CN"


def test_probe_original_subtitle_language_ignores_multiple_manual_subtitles(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        payload = '{"subtitles": {"en": [{"ext": "vtt"}], "zh-CN": [{"ext": "vtt"}]}}'
        return subprocess.CompletedProcess(command, 0, stdout=payload, stderr="")

    result = probe_original_subtitle_language("https://example.com/video", runner=runner)

    assert result is None


def test_probe_original_subtitle_language_uses_source_auto_caption_url(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        payload = (
            '{"automatic_captions": {'
            '"zh-CN": [{"url": "https://example.test/caps%3DASR%26lang%3Dzh-CN"}],'
            '"en-zh-CN": [{"url": "https://example.test/caps%3DASR%26lang%3Dzh-CN%26tlang%3Den"}]'
            "}}"
        )
        return subprocess.CompletedProcess(command, 0, stdout=payload, stderr="")

    result = probe_original_subtitle_language("https://example.com/video", runner=runner)

    assert result == "zh-CN"
