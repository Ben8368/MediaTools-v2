"""Tests for concurrent fetch lock pool behavior."""

from __future__ import annotations

import threading
import time

from mediatools.core.fetch_postprocess import (
    cleanup_output_dir_locks,
    output_dir_lock,
)


def test_concurrent_lock_acquisition_uses_same_lock_object(tmp_path):
    """Multiple threads acquiring lock for same directory must get the same Lock object."""
    test_dir = tmp_path / "concurrent_test"
    lock_ids: dict[str, int] = {}
    events: list[str] = []

    def worker(name: str, delay: float) -> None:
        time.sleep(delay)
        events.append(f"{name}: acquiring")
        lock = output_dir_lock(test_dir)
        lock_ids[name] = id(lock)
        with lock:
            events.append(f"{name}: in_critical")
            time.sleep(0.05)
        cleanup_output_dir_locks(test_dir)
        events.append(f"{name}: cleaned")

    threads = [
        threading.Thread(target=worker, args=("A", 0.00)),
        threading.Thread(target=worker, args=("B", 0.01)),
        threading.Thread(target=worker, args=("C", 0.02)),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All threads should have received the same lock object ID
    unique_locks = set(lock_ids.values())
    assert len(unique_locks) == 1, (
        f"Expected all threads to use the same lock object, "
        f"but got {len(unique_locks)} different locks: {lock_ids}"
    )


def test_lock_cleanup_with_pending_waiters_does_not_create_new_lock(tmp_path):
    """Lock cleanup by one thread must not cause another waiting thread to get a new lock."""
    test_dir = tmp_path / "race_test"
    lock_ids: dict[str, int] = {}
    barrier = threading.Barrier(3)

    def worker_a() -> None:
        lock = output_dir_lock(test_dir)
        lock_ids["A"] = id(lock)
        with lock:
            barrier.wait()  # Wait for B and C to attempt acquisition
            time.sleep(0.1)  # Hold the lock while B and C wait
            cleanup_output_dir_locks(test_dir)  # Clean up while holding lock

    def worker_b() -> None:
        time.sleep(0.01)  # Ensure A acquires first
        lock = output_dir_lock(test_dir)
        lock_ids["B"] = id(lock)
        barrier.wait()
        with lock:
            pass
        cleanup_output_dir_locks(test_dir)

    def worker_c() -> None:
        time.sleep(0.05)  # Arrive after A has cleaned up
        lock = output_dir_lock(test_dir)
        lock_ids["C"] = id(lock)
        barrier.wait()
        with lock:
            pass
        cleanup_output_dir_locks(test_dir)

    threads = [
        threading.Thread(target=worker_a),
        threading.Thread(target=worker_b),
        threading.Thread(target=worker_c),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    unique_locks = set(lock_ids.values())
    assert len(unique_locks) == 1, (
        f"Reference counting must prevent new lock creation when threads are waiting. "
        f"Got {len(unique_locks)} locks: {lock_ids}"
    )


def test_lock_refcount_reaches_zero_after_all_threads_finish(tmp_path):
    """Lock should be removed from pool only after all threads have cleaned up."""
    from mediatools.core.fetch_postprocess import (
        _OUTPUT_DIR_LOCK_REFCOUNTS,
        _OUTPUT_DIR_LOCKS,
    )

    test_dir = tmp_path / "refcount_test"

    def worker() -> None:
        lock = output_dir_lock(test_dir)
        with lock:
            time.sleep(0.02)
        cleanup_output_dir_locks(test_dir)

    threads = [threading.Thread(target=worker) for _ in range(3)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # After all threads finish and clean up, lock should be removed
    assert test_dir not in _OUTPUT_DIR_LOCKS, "Lock should be removed after all threads exit"
    assert (
        test_dir not in _OUTPUT_DIR_LOCK_REFCOUNTS
    ), "Refcount should be removed after all threads exit"
