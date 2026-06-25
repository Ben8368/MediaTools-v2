"""Fetch output post-processing helpers."""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from mediatools.core.fetch_naming import SUBTITLE_EXTS, SUBTITLE_LANG_RE

_OUTPUT_DIR_LOCKS: dict[Path, Lock] = {}
_OUTPUT_DIR_LOCKS_GUARD = Lock()


def output_dir_lock(output_dir: Path) -> Lock:
    """Return a shared lock for writes and post-processing in one output dir."""
    with _OUTPUT_DIR_LOCKS_GUARD:
        lock = _OUTPUT_DIR_LOCKS.get(output_dir)
        if lock is None:
            lock = Lock()
            _OUTPUT_DIR_LOCKS[output_dir] = lock
        return lock


def cleanup_output_dir_locks(output_dir: Path) -> None:
    """Remove the lock entry for a finished output directory.

    Prevents unbounded growth of ``_OUTPUT_DIR_LOCKS`` in long-lived
    sessions or daemon scenarios.  For a one-shot CLI process this is
    a no-op (process exits and the OS reclaims memory).
    """
    with _OUTPUT_DIR_LOCKS_GUARD:
        _OUTPUT_DIR_LOCKS.pop(output_dir, None)


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
