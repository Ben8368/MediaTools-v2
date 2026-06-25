"""Configuration and workspace directory management.

Provides cross-platform directory conventions for configuration, cache, and workspace.
Follows native conventions on Windows/macOS and XDG Base Directory on Linux/Unix.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from mediatools.core.paths import normalize


def _platform_dir(
    *,
    win_suffix: str,
    darwin_suffix: str,
    linux_xdg_env: str,
    linux_xdg_suffix: str,
    linux_fallback_suffix: str,
) -> Path:
    """Return a platform-appropriate directory path based on the given suffixes.

    Resolution order (matches the previous per-function logic exactly):

    1. **Windows**: ``%LOCALAPPDATA%/<win_suffix>``, falling back to
       ``~/AppData/Local/<win_suffix>``.
    2. **XDG** (all Unix, including macOS when the env var is set): ``$<env>/<suffix>``.
    3. **macOS** (no XDG override): ``~/<darwin_suffix>``.
    4. **Linux / other Unix**: ``~/<linux_fallback_suffix>``.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base).joinpath(*win_suffix.split("/"))
        return normalize("~") / "AppData" / "Local" / win_suffix

    xdg_value = os.environ.get(linux_xdg_env)
    if xdg_value:
        return Path(xdg_value, linux_xdg_suffix)

    if sys.platform == "darwin":
        return normalize("~").joinpath(*darwin_suffix.split("/"))

    return normalize("~").joinpath(*linux_fallback_suffix.split("/"))


def get_config_dir() -> Path:
    """Return the configuration directory for MediaTools.

    Follows platform conventions:
    - Linux/Unix: $XDG_CONFIG_HOME/mediatools or ~/.config/mediatools
    - macOS: ~/Library/Application Support/mediatools
    - Windows: %LOCALAPPDATA%\\mediatools

    Returns:
        Absolute path to the config directory.
    """
    return _platform_dir(
        win_suffix="mediatools",
        darwin_suffix="Library/Application Support/mediatools",
        linux_xdg_env="XDG_CONFIG_HOME",
        linux_xdg_suffix="mediatools",
        linux_fallback_suffix=".config/mediatools",
    )


def get_cache_dir() -> Path:
    """Return the cache directory for MediaTools.

    Follows platform conventions:
    - Linux/Unix: $XDG_CACHE_HOME/mediatools or ~/.cache/mediatools
    - macOS: ~/Library/Caches/mediatools
    - Windows: %LOCALAPPDATA%\\mediatools\\cache

    Returns:
        Absolute path to the cache directory.
    """
    return _platform_dir(
        win_suffix="mediatools/cache",
        darwin_suffix="Library/Caches/mediatools",
        linux_xdg_env="XDG_CACHE_HOME",
        linux_xdg_suffix="mediatools",
        linux_fallback_suffix=".cache/mediatools",
    )


def get_data_dir() -> Path:
    """Return the data directory for MediaTools.

    Follows platform conventions:
    - Linux/Unix: $XDG_DATA_HOME/mediatools or ~/.local/share/mediatools
    - macOS: ~/Library/Application Support/mediatools/data
    - Windows: %LOCALAPPDATA%\\mediatools\\data

    Returns:
        Absolute path to the data directory.
    """
    return _platform_dir(
        win_suffix="mediatools/data",
        darwin_suffix="Library/Application Support/mediatools/data",
        linux_xdg_env="XDG_DATA_HOME",
        linux_xdg_suffix="mediatools",
        linux_fallback_suffix=".local/share/mediatools",
    )


def ensure_dir(path: Path) -> Path:
    """Create a directory if it doesn't exist and return it.

    Args:
        path: Directory path to ensure exists.

    Returns:
        The same path, resolved to absolute form.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def load_user_config() -> dict[str, object]:
    """Load user configuration from config.json in the config directory.

    Returns:
        Parsed configuration dict, or empty dict if file does not exist or is invalid.

    Example config.json:
        {
            "max_concurrent_downloads": 4,
            "default_subtitle_language": "en"
        }
    """
    config_file = get_config_dir() / "config.json"
    if not config_file.exists():
        return {}

    try:
        text = config_file.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, dict):
            return {}
        return data
    except (OSError, json.JSONDecodeError):
        return {}


def get_max_concurrent_downloads(default: int = 8) -> int:
    """Return the max concurrent downloads setting from config or default.

    Args:
        default: Fallback value if not configured (default: 8).

    Returns:
        Configured max_concurrent_downloads, clamped to range [1, 16].
    """
    config = load_user_config()
    value = config.get("max_concurrent_downloads", default)
    if not isinstance(value, int):
        return default
    return max(1, min(value, 16))
