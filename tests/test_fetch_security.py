from __future__ import annotations

import subprocess

import pytest

from mediatools.core.errors import MediaToolsError
from mediatools.core.fetch import FetchOptions, build_fetch_args, fetch_many, probe_language


def test_fetch_many_rejects_non_http_url_before_runner(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    calls: list[list[str]] = []

    def runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [FetchOptions(url="file:///tmp/video", output_dir=tmp_path)],
        runner=runner,
    )

    assert calls == []
    assert result.failed == 1
    assert "http or https" in str(result.items[0].error)


def test_probe_language_rejects_non_http_url_before_runner(tmp_path, monkeypatch):
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    calls: list[list[str]] = []

    def runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    with pytest.raises(MediaToolsError):
        probe_language("file:///tmp/video", runner=runner)

    assert calls == []


@pytest.mark.parametrize(
    "template",
    [
        "/tmp/%(title)s.%(ext)s",
        r"C:\tmp\%(title)s.%(ext)s",
        "../%(title)s.%(ext)s",
        "sub/../../%(title)s.%(ext)s",
    ],
)
def test_build_fetch_args_rejects_output_template_path_escape(tmp_path, template):
    with pytest.raises(MediaToolsError):
        build_fetch_args(
            FetchOptions(
                url="https://example.com/video",
                output_dir=tmp_path,
                output_template=template,
            ),
        )


def test_build_fetch_args_allows_safe_template_subdirectories(tmp_path):
    args = build_fetch_args(
        FetchOptions(
            url="https://example.com/video",
            output_dir=tmp_path,
            output_template="series/%(title)s.%(ext)s",
        ),
    )

    idx = args.index("--output")
    assert args[idx + 1] == "series/%(title)s.%(ext)s"
