"""Tests for configuration and workspace directory management."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from mediatools.core.config import (
    ensure_dir,
    get_cache_dir,
    get_config_dir,
    get_data_dir,
    get_max_concurrent_downloads,
    load_user_config,
)


def test_get_config_dir_respects_xdg_on_unix():
    """get_config_dir should use XDG_CONFIG_HOME when set on Unix."""
    if sys.platform == "win32":
        pytest.skip("Unix-specific test")

    with patch.dict("os.environ", {"XDG_CONFIG_HOME": "/tmp/config"}):
        config_dir = get_config_dir()
        assert config_dir == Path("/tmp/config/mediatools")


def test_get_config_dir_defaults_to_dotconfig_on_unix():
    """get_config_dir should default to ~/.config/mediatools on Unix."""
    if sys.platform in {"win32", "darwin"}:
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


def test_get_config_dir_defaults_to_application_support_on_macos():
    """get_config_dir should default to Application Support on macOS."""
    with patch("sys.platform", "darwin"):
        with patch.dict("os.environ", {}, clear=True):
            with patch("mediatools.core.config.normalize") as mock_normalize:
                mock_normalize.return_value = Path("/Users/test")
                config_dir = get_config_dir()
                assert config_dir == Path("/Users/test/Library/Application Support/mediatools")


def test_get_cache_dir_respects_xdg_on_unix():
    """get_cache_dir should use XDG_CACHE_HOME when set on Unix."""
    if sys.platform == "win32":
        pytest.skip("Unix-specific test")

    with patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/cache"}):
        cache_dir = get_cache_dir()
        assert cache_dir == Path("/tmp/cache/mediatools")


def test_get_cache_dir_defaults_to_dotcache_on_unix():
    """get_cache_dir should default to ~/.cache/mediatools on Unix."""
    if sys.platform in {"win32", "darwin"}:
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


def test_get_cache_dir_defaults_to_library_caches_on_macos():
    """get_cache_dir should default to Library/Caches on macOS."""
    with patch("sys.platform", "darwin"):
        with patch.dict("os.environ", {}, clear=True):
            with patch("mediatools.core.config.normalize") as mock_normalize:
                mock_normalize.return_value = Path("/Users/test")
                cache_dir = get_cache_dir()
                assert cache_dir == Path("/Users/test/Library/Caches/mediatools")


def test_get_data_dir_respects_xdg_on_unix():
    """get_data_dir should use XDG_DATA_HOME when set on Unix."""
    if sys.platform == "win32":
        pytest.skip("Unix-specific test")

    with patch.dict("os.environ", {"XDG_DATA_HOME": "/tmp/data"}):
        data_dir = get_data_dir()
        assert data_dir == Path("/tmp/data/mediatools")


def test_get_data_dir_defaults_to_local_share_on_unix():
    """get_data_dir should default to ~/.local/share/mediatools on Unix."""
    if sys.platform in {"win32", "darwin"}:
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


def test_get_data_dir_defaults_to_application_support_data_on_macos():
    """get_data_dir should default to Application Support data on macOS."""
    with patch("sys.platform", "darwin"):
        with patch.dict("os.environ", {}, clear=True):
            with patch("mediatools.core.config.normalize") as mock_normalize:
                mock_normalize.return_value = Path("/Users/test")
                data_dir = get_data_dir()
                assert data_dir == Path("/Users/test/Library/Application Support/mediatools/data")


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


def test_load_user_config_returns_empty_dict_when_file_missing(tmp_path):
    """load_user_config returns empty dict when config.json does not exist."""
    with patch("mediatools.core.config.get_config_dir", return_value=tmp_path):
        config = load_user_config()
        assert config == {}


def test_load_user_config_returns_empty_dict_on_invalid_json(tmp_path):
    """load_user_config returns empty dict when config.json is invalid JSON."""
    config_file = tmp_path / "config.json"
    config_file.write_text("{invalid json", encoding="utf-8")

    with patch("mediatools.core.config.get_config_dir", return_value=tmp_path):
        config = load_user_config()
        assert config == {}


def test_load_user_config_returns_parsed_dict(tmp_path):
    """load_user_config returns parsed dict from valid config.json."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"max_concurrent_downloads": 4}', encoding="utf-8")

    with patch("mediatools.core.config.get_config_dir", return_value=tmp_path):
        config = load_user_config()
        assert config == {"max_concurrent_downloads": 4}


def test_get_max_concurrent_downloads_returns_default_when_not_configured(tmp_path):
    """get_max_concurrent_downloads returns default when config.json missing."""
    with patch("mediatools.core.config.get_config_dir", return_value=tmp_path):
        result = get_max_concurrent_downloads(default=8)
        assert result == 8


def test_get_max_concurrent_downloads_returns_configured_value(tmp_path):
    """get_max_concurrent_downloads returns value from config.json."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"max_concurrent_downloads": 4}', encoding="utf-8")

    with patch("mediatools.core.config.get_config_dir", return_value=tmp_path):
        result = get_max_concurrent_downloads(default=8)
        assert result == 4


def test_get_max_concurrent_downloads_clamps_to_minimum(tmp_path):
    """get_max_concurrent_downloads clamps values below 1 to 1."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"max_concurrent_downloads": -5}', encoding="utf-8")

    with patch("mediatools.core.config.get_config_dir", return_value=tmp_path):
        result = get_max_concurrent_downloads(default=8)
        assert result == 1


def test_get_max_concurrent_downloads_clamps_to_maximum(tmp_path):
    """get_max_concurrent_downloads clamps values above 16 to 16."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"max_concurrent_downloads": 100}', encoding="utf-8")

    with patch("mediatools.core.config.get_config_dir", return_value=tmp_path):
        result = get_max_concurrent_downloads(default=8)
        assert result == 16


def test_get_max_concurrent_downloads_returns_default_on_invalid_type(tmp_path):
    """get_max_concurrent_downloads returns default when value is not an int."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"max_concurrent_downloads": "four"}', encoding="utf-8")

    with patch("mediatools.core.config.get_config_dir", return_value=tmp_path):
        result = get_max_concurrent_downloads(default=8)
        assert result == 8
