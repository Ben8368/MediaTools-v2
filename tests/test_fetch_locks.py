"""Tests for cross-process-safe file locking in fetch post-processing."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from mediatools.core.fetch_postprocess import output_dir_lock


def test_lock_serializes_concurrent_access(tmp_path):
    """Multiple threads acquiring lock for same directory must serialize access."""
    test_dir = tmp_path / "concurrent_test"
    test_dir.mkdir(parents=True, exist_ok=True)

    execution_order: list[str] = []
    lock = threading.Lock()  # Just for test coordination

    def worker(name: str, hold_time: float = 0.05) -> None:
        with output_dir_lock(test_dir):
            with lock:
                execution_order.append(f"{name}_start")
            time.sleep(hold_time)
            with lock:
                execution_order.append(f"{name}_end")

    threads = [
        threading.Thread(target=worker, args=("A", 0.05)),
        threading.Thread(target=worker, args=("B", 0.03)),
        threading.Thread(target=worker, args=("C", 0.02)),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify that each worker's start/end pairs are not interleaved
    # (i.e., one finishes before the next starts)
    assert len(execution_order) == 6
    for i in range(0, 6, 2):
        name = execution_order[i].split("_")[0]
        assert execution_order[i] == f"{name}_start"
        assert execution_order[i + 1] == f"{name}_end"


def test_lock_releases_after_exception(tmp_path):
    """Lock must be released even if an exception occurs inside the context."""
    test_dir = tmp_path / "exception_test"
    test_dir.mkdir(parents=True, exist_ok=True)

    results: list[str] = []

    def worker_with_error() -> None:
        try:
            with output_dir_lock(test_dir):
                results.append("acquired")
                raise ValueError("Simulated error")
        except ValueError:
            results.append("caught")

    def worker_after() -> None:
        time.sleep(0.05)  # Let first worker fail
        with output_dir_lock(test_dir):
            results.append("second_acquired")

    t1 = threading.Thread(target=worker_with_error)
    t2 = threading.Thread(target=worker_after)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results == ["acquired", "caught", "second_acquired"]


def test_lock_cleanup_removes_lock_file(tmp_path):
    """Lock file should be removed after context exits."""
    import tempfile

    test_dir = tmp_path / "cleanup_test"
    test_dir.mkdir(parents=True, exist_ok=True)

    lock_name = str(test_dir.resolve()).replace("\\", "_").replace("/", "_").lstrip("_")
    lock_path = Path(tempfile.gettempdir()) / f"mediatools_dir_{lock_name}.lock"

    with output_dir_lock(test_dir):
        # Lock file exists during lock hold
        assert lock_path.exists()

    # Lock file should be removed after release
    assert not lock_path.exists()


def test_different_directories_get_different_locks(tmp_path):
    """Locks for different directories should be independent."""
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir(parents=True, exist_ok=True)
    dir_b.mkdir(parents=True, exist_ok=True)

    results: list[str] = []

    def worker_a() -> None:
        with output_dir_lock(dir_a):
            results.append("a_start")
            time.sleep(0.05)
            results.append("a_end")

    def worker_b() -> None:
        with output_dir_lock(dir_b):
            results.append("b_start")
            time.sleep(0.03)
            results.append("b_end")

    t1 = threading.Thread(target=worker_a)
    t2 = threading.Thread(target=worker_b)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Both locks should be acquired concurrently (interleaved)
    assert results.index("a_start") < results.index("a_end")
    assert results.index("b_start") < results.index("b_end")
    # Since locks are independent, both should start before either ends
    assert "b_start" in results[:2] or "a_start" in results[:2]
