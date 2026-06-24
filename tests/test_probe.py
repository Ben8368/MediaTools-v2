from __future__ import annotations

import json
import subprocess

from mediatools.core.probe import build_probe_args, format_probe_text, probe_media, summarize_probe


def test_build_probe_args_uses_json_output(tmp_path):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"demo")

    args = build_probe_args(media)

    assert "-show_streams" in args
    assert "-show_format" in args
    assert str(media.resolve()) in args


def test_probe_media_parses_ffprobe_json(tmp_path, monkeypatch):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"demo")
    payload = {"format": {"duration": "1.23"}, "streams": []}
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload), stderr="")

    data = probe_media(media, runner=runner)

    assert data["format"]["duration"] == "1.23"


def test_summarize_probe_extracts_video_and_audio():
    summary = summarize_probe(
        {
            "format": {"duration": "10.0", "format_name": "mov,mp4", "bit_rate": "1000"},
            "streams": [
                {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
                {"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "channels": 2},
            ],
        },
    )

    assert summary["video"]["width"] == 1920
    assert summary["audio"]["codec_name"] == "aac"
    assert "Duration: 10.0" in format_probe_text(summary)
