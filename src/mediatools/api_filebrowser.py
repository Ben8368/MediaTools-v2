"""Small filesystem browser helpers for the local v2 API."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from mediatools.core.paths import normalize

JsonReader = Callable[[BaseHTTPRequestHandler], dict[str, object]]
JsonResponder = Callable[[BaseHTTPRequestHandler, object, int], None]


def _entry_payload(path: Path) -> dict[str, object]:
    stat = path.stat()
    entry_type = "directory" if path.is_dir() else "file"
    return {
        "name": path.name or str(path),
        "path": str(path),
        "size": 0 if entry_type == "directory" else stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
        "type": entry_type,
        "extension": path.suffix if entry_type == "file" else "",
    }


def _disk_payload(path: Path, name: str) -> dict[str, object]:
    usage = shutil.disk_usage(path)
    return {
        "name": name,
        "path": str(path),
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
    }


def workspace_payload() -> dict[str, object]:
    root = normalize(Path.cwd())
    return {"workspace": {"project_root": str(root)}, "project_root": str(root)}


def list_disks() -> dict[str, object]:
    disks: list[dict[str, object]] = []
    if os.name == "nt":
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{letter}:\\")
            if drive.exists():
                try:
                    disks.append(_disk_payload(drive, f"本地磁盘 ({letter}:)"))
                except OSError:
                    continue
    else:
        disks.append(_disk_payload(Path("/"), "根目录 /"))
    return {"ok": True, "disks": disks}


def list_directory(directory: object) -> dict[str, object]:
    path = normalize(str(directory or "."))
    if not path.exists():
        raise FileNotFoundError(f"目录不存在: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"不是目录: {path}")

    directories: list[dict[str, object]] = []
    files: list[dict[str, object]] = []
    for child in path.iterdir():
        try:
            if child.is_dir():
                directories.append(_entry_payload(child))
            elif child.is_file():
                files.append(_entry_payload(child))
        except OSError:
            continue

    directories.sort(key=lambda item: str(item["name"]).lower())
    files.sort(key=lambda item: str(item["name"]).lower())
    return {"ok": True, "path": str(path), "directories": directories, "files": files}


def create_directory(path_value: object) -> dict[str, object]:
    path = normalize(str(path_value or ""))
    if not str(path_value or "").strip():
        raise ValueError("缺少目录路径")
    path.mkdir(parents=True, exist_ok=True)
    return {"ok": True, "path": str(path)}


def handle_list_directory_request(
    handler: BaseHTTPRequestHandler,
    read_json: JsonReader,
    json_response: JsonResponder,
) -> None:
    try:
        draft = read_json(handler)
        json_response(handler, list_directory(draft.get("directory")), 200)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        json_response(handler, {"error": str(exc)}, 400)
    except OSError as exc:
        json_response(handler, {"error": str(exc)}, 500)


def handle_create_directory_request(
    handler: BaseHTTPRequestHandler,
    read_json: JsonReader,
    json_response: JsonResponder,
) -> None:
    try:
        draft = read_json(handler)
        json_response(handler, create_directory(draft.get("path")), 201)
    except ValueError as exc:
        json_response(handler, {"error": str(exc)}, 400)
    except OSError as exc:
        json_response(handler, {"error": str(exc)}, 500)
