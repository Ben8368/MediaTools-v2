"""Tests for configuration and workspace directory management."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from mediatools.core.config import ensure_dir, get_cache_dir, get_config_dir, get_data_dir


def test_get_config_dir_respects_xdg_on_unix():
    """get_config_dir should use XDG_CONFIG_HOME when set on Unix."""
    if sys.platform == "win32":
        pytest.skip("Unix-specific test")

    with patch.dict("os.environ", {"XDG_CONFIG_HOME": "/tmp/config"}):
        config_dir = get_config_dir()
        assert config_dir == Path("/tmp/config/mediatools")


def test_get_config_dir_defaults_to_dotconfig_on_unix():
    """get_config_dir should default to ~/.config/mediatools on Unix."""
    if sys.platform == "win32":
        pytest.skip("Unix-specific test")

    with patch.dict("os.environ", {}, clear=True):
        with patch("mediatools.core.config.normalize") as mock_normalize:
            mock_normalize.return_value = Path("/home/user")
            config_dir = get_config_dir()
            assert config_dir == Path("/home/user/.config/mediatools")


def test_get_config_dir_uses_localappdata_on_windows():
    """get_config_dir should use LOCALAPPDATA on Windows."""
    if sys.platform != "win32":
        pytest.skip("Windows-specific test")

    with patch.dict("os.environ", {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}):
        config_dir = get_config_dir()
        assert config_dir == Path("C:/Users/test/AppData/Local/mediatools")


def test_get_cache_dir_respects_xdg_on_unix():
    """get_cache_dir should use XDG_CACHE_HOME when set on Unix."""
    if sys.platform == "win32":
        pytest.skip("Unix-specific test")

    with patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/cache"}):
        cache_dir = get_cache_dir()
        assert cache_dir == Path("/tmp/cache/mediatools")


def test_get_cache_dir_defaults_to_dotcache_on_unix():
    """get_cache_dir should default to ~/.cache/mediatools on Unix."""
    if sys.platform == "win32":
        pytest.skip("Unix-specific test")

    with patch.dict("os.environ", {}, clear=True):
        with patch("mediatools.core.config.normalize") as mock_normalize:
            mock_normalize.return_value = Path("/home/user")
            cache_dir = get_cache_dir()
            assert cache_dir == Path("/home/user/.cache/mediatools")


def test_get_cache_dir_uses_localappdata_on_windows():
    """get_cache_dir should use LOCALAPPDATA on Windows."""
    if sys.platform != "win32":
        pytest.skip("Windows-specific test")

    with patch.dict("os.environ", {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}):
        cache_dir = get_cache_dir()
        assert cache_dir == Path("C:/Users/test/AppData/Local/mediatools/cache")


def test_get_data_dir_respects_xdg_on_unix():
    """get_data_dir should use XDG_DATA_HOME when set on Unix."""
    if sys.platform == "win32":
        pytest.skip("Unix-specific test")

    with patch.dict("os.environ", {"XDG_DATA_HOME": "/tmp/data"}):
        data_dir = get_data_dir()
        assert data_dir == Path("/tmp/data/mediatools")


def test_get_data_dir_defaults_to_local_share_on_unix():
    """get_data_dir should default to ~/.local/share/mediatools on Unix."""
    if sys.platform == "win32":
        pytest.skip("Unix-specific test")

    with patch.dict("os.environ", {}, clear=True):
        with patch("mediatools.core.config.normalize") as mock_normalize:
            mock_normalize.return_value = Path("/home/user")
            data_dir = get_data_dir()
            assert data_dir == Path("/home/user/.local/share/mediatools")


def test_get_data_dir_uses_localappdata_on_windows():
    """get_data_dir should use LOCALAPPDATA on Windows."""
    if sys.platform != "win32":
        pytest.skip("Windows-specific test")

    with patch.dict("os.environ", {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}):
        data_dir = get_data_dir()
        assert data_dir == Path("C:/Users/test/AppData/Local/mediatools/data")


def test_ensure_dir_creates_directory(tmp_path):
    """ensure_dir should create the directory if it doesn't exist."""
    target = tmp_path / "new" / "nested" / "dir"
    assert not target.exists()

    result = ensure_dir(target)

    assert target.exists()
    assert target.is_dir()
    assert result == target.resolve()


def test_ensure_dir_is_idempotent(tmp_path):
    """ensure_dir should work on existing directories."""
    target = tmp_path / "existing"
    target.mkdir()

    result = ensure_dir(target)

    assert target.exists()
    assert result == target.resolve()


def test_ensure_dir_returns_absolute_path(tmp_path):
    """ensure_dir should return an absolute resolved path."""
    relative = Path("relative/path")
    # Create under tmp_path to avoid polluting working directory
    target = tmp_path / relative

    result = ensure_dir(target)

    assert result.is_absolute()
    assert result == target.resolve()
