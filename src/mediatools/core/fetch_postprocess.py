"""Fetch output post-processing helpers."""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

from mediatools.core.fetch_naming import SUBTITLE_EXTS, SUBTITLE_LANG_RE


@contextlib.contextmanager
def output_dir_lock(output_dir: Path) -> Iterator[None]:
    """Yield a context manager that serializes access to one output directory.

    Uses a filesystem-based lock file so that **multiple MediaTools processes**
    downloading to the same directory cannot corrupt each other's subtitle
    post-processing.  The lock file is created in the system temp directory
    with a name derived from the resolved output directory path.

    On Windows, uses ``msvcrt.locking`` for exclusive byte-range locking.
    On POSIX, uses ``fcntl.flock`` for advisory file locking.
    """
    resolved = output_dir.resolve()
    lock_name = str(resolved).replace(os.sep, "_").lstrip("_")
    lock_path = Path(tempfile.gettempdir()) / f"mediatools_dir_{lock_name}.lock"

    lock_fd = open(lock_path, "w")  # noqa: SIM115 — simple temp lock file
    try:
        if sys.platform == "win32":
            import msvcrt

            # Lock the entire file (1 byte at offset 0, length 1 MB covers typical use).
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_LOCK, 1024 * 1024)
        else:
            import fcntl

            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        if sys.platform == "win32":
            import msvcrt

            try:
                msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1024 * 1024)
            except OSError:
                pass  # Already closed or unlocked
        else:
            import fcntl

            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
        with contextlib.suppress(OSError):
            lock_path.unlink(missing_ok=True)


def subtitle_snapshot(output_dir: Path) -> dict[str, tuple[int, int]]:
    """Record subtitle file state before yt-dlp runs."""
    snapshot: dict[str, tuple[int, int]] = {}
    if not output_dir.is_dir():
        return snapshot
    for child in output_dir.iterdir():
        if not is_language_subtitle(child):
            continue
        try:
            stat = child.stat()
        except OSError:
            continue
        snapshot[child.name] = (stat.st_size, stat.st_mtime_ns)
    return snapshot


def changed_subtitles(output_dir: Path, before: dict[str, tuple[int, int]]) -> tuple[Path, ...]:
    """Return subtitle files created or changed by the just-finished download."""
    changed: list[Path] = []
    if not output_dir.is_dir():
        return ()
    for child in output_dir.iterdir():
        if not is_language_subtitle(child):
            continue
        try:
            stat = child.stat()
        except OSError:
            continue
        state = (stat.st_size, stat.st_mtime_ns)
        if before.get(child.name) != state:
            changed.append(child)
    return tuple(changed)


def is_language_subtitle(path: Path) -> bool:
    """Return True for subtitle files with a language middle segment."""
    return path.is_file() and path.suffix.lower() in SUBTITLE_EXTS and bool(
        SUBTITLE_LANG_RE.match(path.name),
    )
