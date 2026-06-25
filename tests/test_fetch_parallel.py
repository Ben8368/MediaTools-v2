"""Tests for concurrent fetch execution (``max_workers > 1``)."""

from __future__ import annotations

import concurrent.futures
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


def test_fetch_many_concurrent_keeps_duplicate_urls_as_separate_items(tmp_path, monkeypatch):
    """Duplicate URLs should not overwrite each other in the result summary."""
    monkeypatch.setattr("mediatools.core.ffmpeg.shutil.which", lambda tool: f"/bin/{tool}")
    download_count = 0

    def runner(command, **kwargs):
        nonlocal download_count
        if "--print" not in command:
            download_count += 1
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_many(
        [
            FetchOptions(url="https://example.com/same", output_dir=tmp_path / "one"),
            FetchOptions(url="https://example.com/same", output_dir=tmp_path / "two"),
        ],
        runner=runner,
        max_workers=2,
    )

    assert result.total == 2
    assert result.succeeded == 2
    assert download_count == 2
    assert result.items[0].output_dir == (tmp_path / "one").resolve()
    assert result.items[1].output_dir == (tmp_path / "two").resolve()


def test_fetch_many_concurrent_interrupt_shuts_down_without_wait(tmp_path, monkeypatch):
    class FakeFuture:
        def __init__(self) -> None:
            self.cancelled = False

        def cancel(self) -> None:
            self.cancelled = True

    class FakeExecutor:
        def __init__(self, max_workers):
            self.max_workers = max_workers
            self.futures: list[FakeFuture] = []
            self.shutdown_call: tuple[bool, bool] | None = None

        def submit(self, *args, **kwargs):
            future = FakeFuture()
            self.futures.append(future)
            return future

        def shutdown(self, *, wait=True, cancel_futures=False):
            self.shutdown_call = (wait, cancel_futures)

    fake_executor = FakeExecutor(max_workers=2)

    def fake_executor_factory(max_workers):
        assert max_workers == 2
        return fake_executor

    def interrupted_as_completed(futures):
        raise KeyboardInterrupt
        yield from futures

    monkeypatch.setattr(concurrent.futures, "ThreadPoolExecutor", fake_executor_factory)
    monkeypatch.setattr(concurrent.futures, "as_completed", interrupted_as_completed)

    result = fetch_many(
        [
            FetchOptions(url="https://example.com/a", output_dir=tmp_path),
            FetchOptions(url="https://example.com/b", output_dir=tmp_path),
        ],
        max_workers=2,
    )

    assert result.failed == 2
    assert all("Interrupted by user" in str(item.error) for item in result.items)
    assert all(future.cancelled for future in fake_executor.futures)
    assert fake_executor.shutdown_call == (False, True)
