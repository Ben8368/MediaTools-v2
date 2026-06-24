"""Configuration and workspace directory management.

Provides cross-platform directory conventions for configuration, cache, and workspace.
Follows native conventions on Windows/macOS and XDG Base Directory on Linux/Unix.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from mediatools.core.paths import normalize


def get_config_dir() -> Path:
    """Return the configuration directory for MediaTools.

    Follows platform conventions:
    - Linux/Unix: $XDG_CONFIG_HOME/mediatools or ~/.config/mediatools
    - macOS: ~/Library/Application Support/mediatools
    - Windows: %LOCALAPPDATA%\\mediatools

    Returns:
        Absolute path to the config directory.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "mediatools"
        return normalize("~") / "AppData" / "Local" / "mediatools"

    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "mediatools"
    if sys.platform == "darwin":
        return normalize("~") / "Library" / "Application Support" / "mediatools"
    return normalize("~") / ".config" / "mediatools"


def get_cache_dir() -> Path:
    """Return the cache directory for MediaTools.

    Follows platform conventions:
    - Linux/Unix: $XDG_CACHE_HOME/mediatools or ~/.cache/mediatools
    - macOS: ~/Library/Caches/mediatools
    - Windows: %LOCALAPPDATA%\\mediatools\\cache

    Returns:
        Absolute path to the cache directory.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "mediatools" / "cache"
        return normalize("~") / "AppData" / "Local" / "mediatools" / "cache"

    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache) / "mediatools"
    if sys.platform == "darwin":
        return normalize("~") / "Library" / "Caches" / "mediatools"
    return normalize("~") / ".cache" / "mediatools"


def get_data_dir() -> Path:
    """Return the data directory for MediaTools.

    Follows platform conventions:
    - Linux/Unix: $XDG_DATA_HOME/mediatools or ~/.local/share/mediatools
    - macOS: ~/Library/Application Support/mediatools/data
    - Windows: %LOCALAPPDATA%\\mediatools\\data

    Returns:
        Absolute path to the data directory.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "mediatools" / "data"
        return normalize("~") / "AppData" / "Local" / "mediatools" / "data"

    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "mediatools"
    if sys.platform == "darwin":
        return normalize("~") / "Library" / "Application Support" / "mediatools" / "data"
    return normalize("~") / ".local" / "share" / "mediatools"


def ensure_dir(path: Path) -> Path:
    """Create a directory if it doesn't exist and return it.

    Args:
        path: Directory path to ensure exists.

    Returns:
        The same path, resolved to absolute form.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()
