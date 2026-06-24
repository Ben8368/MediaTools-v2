from __future__ import annotations

import subprocess

import pytest

from mediatools.core.encode import EncodeOptions, build_encode_args, encode_media
from mediatools.core.errors import MediaFileError


def test_build_encode_args_for_audio_extraction(tmp_path):
    options = EncodeOptions(
        input_path=tmp_path / "in.mp4",
        output_path=tmp_path / "out.mp3",
        extract_audio=True,
    )

    args = build_encode_args(options)

    assert "-vn" in args
    assert ["-c:a", "libmp3lame"] == args[args.index("-c:a") : args.index("-c:a") + 2]


def test_build_encode_args_for_transcode(tmp_path):
    options = EncodeOptions(
        input_path=tmp_path / "in.mp4",
        output_path=tmp_path / "out.mp4",
        video_codec="libx265",
        audio_codec="aac",
        video_bitrate="2M",
        overwrite=True,
    )

    args = build_encode_args(options)

    assert args[0] == "-y"
    assert "-c:v" in args
    assert "libx265" in args
    assert "-b:v" in args


def test_encode_media_rejects_existing_output_without_overwrite(tmp_path):
    source = tmp_path / "in.mp4"
    output = tmp_path / "out.mp4"
    source.write_bytes(b"input")
    output.write_bytes(b"existing")

    with pytest.raises(MediaFileError):
        encode_media(EncodeOptions(input_path=source, output_path=output))


def test_encode_media_runs_ffmpeg(tmp_path, monkeypatch):
    source = tmp_path / "in.mp4"
    output = tmp_path / "out.mp4"
    source.write_bytes(b"input")
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = encode_media(EncodeOptions(input_path=source, output_path=output), runner=runner)

    assert result.command[0] == "/bin/ffmpeg"
    assert str(output.resolve()) in result.command
