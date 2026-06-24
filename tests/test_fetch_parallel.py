"""Tests for concurrent fetch execution (``max_workers > 1``)."""

from __future__ import annotations

import subprocess

from mediatools.core.fetch import FetchOptions, fetch_many


def test_fetch_many_serial_is_default(tmp_path):
    """Default max_workers=1 runs serial (no ThreadPoolExecutor)."""
    result = fetch_many(
        [FetchOptions(url="https://example.com/video", output_dir=tmp_path)],
        dry_run=True,
    )
    assert result.planned == 1


def test_fetch_many_concurrent_executes_in_parallel(tmp_path, monkeypatch):
    """max_workers > 1 uses ThreadPoolExecutor and completes all items."""
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    downloads_completed: list[str] = []

    def runner(command, **kwargs):
        # Track only the download step (not language probes that also call yt-dlp).
        if "--skip-download" not in command and "--print" not in command:
            downloads_completed.append(command[-1])
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [
            FetchOptions(url="https://example.com/a", output_dir=tmp_path),
            FetchOptions(url="https://example.com/b", output_dir=tmp_path),
            FetchOptions(url="https://example.com/c", output_dir=tmp_path),
        ],
        runner=runner,
        max_workers=2,
    )

    assert result.succeeded == 3
    assert len(downloads_completed) == 3


def test_fetch_many_concurrent_collects_errors(tmp_path, monkeypatch):
    """One failure should not prevent other concurrent items from succeeding."""
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")

    def runner(command, **kwargs):
        # The URL is always the last argument; check for substring match.
        if "fail" in command[-1]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="download error")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [
            FetchOptions(url="https://example.com/ok1", output_dir=tmp_path),
            FetchOptions(url="https://example.com/fail", output_dir=tmp_path),
            FetchOptions(url="https://example.com/ok2", output_dir=tmp_path),
        ],
        runner=runner,
        max_workers=3,
    )

    assert result.succeeded == 2
    assert result.failed == 1
    assert result.items[1].error == "download error"


def test_fetch_many_concurrent_preserves_results_order(tmp_path, monkeypatch):
    """Results are returned in input order regardless of completion order."""
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    import time

    def runner(command, **kwargs):
        if "slow" in command[-1]:
            time.sleep(0.1)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [
            FetchOptions(url="https://example.com/fast", output_dir=tmp_path),
            FetchOptions(url="https://example.com/slow", output_dir=tmp_path),
        ],
        runner=runner,
        max_workers=2,
    )

    assert result.succeeded == 2
    assert result.items[0].url == "https://example.com/fast"
    assert result.items[1].url == "https://example.com/slow"
