from __future__ import annotations

import subprocess

import pytest

from mediatools.core.errors import MediaToolsError
from mediatools.core.screenshot import (
    ScreenshotOptions,
    build_screenshot_args,
    capture_screenshot,
)


def test_build_single_screenshot_args(tmp_path):
    options = ScreenshotOptions(
        input_path=tmp_path / "in.mp4",
        output_path=tmp_path / "shot.png",
        timestamp="00:00:02",
    )

    args = build_screenshot_args(options)

    assert "-ss" in args
    assert "-frames:v" in args


def test_build_interval_screenshot_args(tmp_path):
    options = ScreenshotOptions(
        input_path=tmp_path / "in.mp4",
        output_path=tmp_path / "frames_%04d.png",
        interval_seconds=5,
    )

    args = build_screenshot_args(options)

    assert "fps=1/5" in args


def test_capture_screenshot_validates_timestamp(tmp_path):
    source = tmp_path / "in.mp4"
    source.write_bytes(b"input")

    with pytest.raises(MediaToolsError):
        capture_screenshot(
            ScreenshotOptions(input_path=source, output_path=tmp_path / "out.png", timestamp="bad"),
        )


def test_capture_screenshot_runs_ffmpeg(tmp_path, monkeypatch):
    source = tmp_path / "in.mp4"
    output = tmp_path / "out.png"
    source.write_bytes(b"input")
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = capture_screenshot(
        ScreenshotOptions(input_path=source, output_path=output),
        runner=runner,
    )

    assert result.command[0] == "/bin/ffmpeg"
    assert str(output.resolve()) in result.command
