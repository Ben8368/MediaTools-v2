from __future__ import annotations

import subprocess

import pytest

from mediatools.core.errors import ExternalToolError
from mediatools.core.ffmpeg import run_tool


def test_run_tool_uses_path_and_returns_result(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    result = run_tool("ffmpeg", ["-version"], runner=runner)

    assert result.command == ("/bin/ffmpeg", "-version")
    assert result.stdout == "ok"


def test_run_tool_raises_when_missing(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: None)

    with pytest.raises(ExternalToolError) as excinfo:
        run_tool("ffmpeg", ["-version"])

    assert excinfo.value.tool == "ffmpeg"


def test_run_tool_raises_on_nonzero(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="bad input")

    with pytest.raises(ExternalToolError) as excinfo:
        run_tool("ffmpeg", ["-bad"], runner=runner)

    assert excinfo.value.returncode == 1
    assert "bad input" in excinfo.value.message


def test_run_tool_uses_errors_replace(monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    captured_kwargs = {}

    def runner(command, **kwargs):
        captured_kwargs.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    run_tool("yt-dlp", ["--version"], runner=runner)

    assert captured_kwargs["encoding"] == "utf-8"
    assert captured_kwargs["errors"] == "replace"
