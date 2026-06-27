"""Tests for local file browser API helpers."""

from __future__ import annotations

from mediatools.api_filebrowser import (
    create_directory,
    list_directory,
    list_disks,
    workspace_payload,
)


def test_workspace_payload_returns_project_root() -> None:
    data = workspace_payload()
    assert data["workspace"]["project_root"]
    assert data["project_root"] == data["workspace"]["project_root"]


def test_list_disks_returns_at_least_one_root() -> None:
    data = list_disks()
    assert data["ok"] is True
    disks = data["disks"]
    assert isinstance(disks, list)
    assert disks
    assert {"name", "path", "total", "used", "free"} <= set(disks[0])


def test_list_directory_splits_folders_and_files(tmp_path) -> None:
    (tmp_path / "folder").mkdir()
    (tmp_path / "clip.mp4").write_text("video", encoding="utf-8")

    data = list_directory(tmp_path)

    assert data["ok"] is True
    assert data["path"] == str(tmp_path.resolve())
    assert data["directories"][0]["name"] == "folder"
    assert data["files"][0]["name"] == "clip.mp4"


def test_create_directory(tmp_path) -> None:
    target = tmp_path / "downloads"
    data = create_directory(target)

    assert data["ok"] is True
    assert data["path"] == str(target.resolve())
    assert target.is_dir()
