"""Cross-platform path helpers built on :mod:`pathlib`."""

from __future__ import annotations

from pathlib import Path


def normalize(path: str | Path) -> Path:
    """Expand ``~`` and return an absolute, resolved path."""
    return Path(path).expanduser().resolve()


def join_under(base: str | Path, *parts: str | Path) -> Path:
    """Join path parts under *base* without resolving the result."""
    return Path(base).joinpath(*parts)


def relative_to_base(path: str | Path, base: str | Path) -> Path:
    """Return *path* relative to *base*.

    Raises:
        ValueError: If *path* is not inside *base* after resolution.
    """
    resolved_path = normalize(path)
    resolved_base = normalize(base)
    return resolved_path.relative_to(resolved_base)


def is_safe_child(path: str | Path, base: str | Path) -> bool:
    """Return True when *path* resolves to a location inside *base*."""
    try:
        relative_to_base(path, base)
        return True
    except ValueError:
        return False
