"""Download response helpers for recorded API task outputs."""

from __future__ import annotations

import mimetypes
import shutil
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import quote

from mediatools.api_tasks import Task


def task_allowed_output_paths(task: Task) -> set[Path]:
    """Return absolute file paths recorded as outputs for a task."""
    paths = {Path(path).resolve() for path in task.output_files if path}
    items = task.result.get("items", [])
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            raw_files = item.get("output_files")
            if isinstance(raw_files, list):
                paths.update(Path(str(path)).resolve() for path in raw_files if path)
    return paths


def download_file_response(handler: BaseHTTPRequestHandler, path: Path) -> None:
    """Send a local task output as an attachment."""
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    filename = quote(path.name)
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(path.stat().st_size))
    handler.send_header(
        "Content-Disposition",
        f"attachment; filename*=UTF-8''{filename}",
    )
    handler.end_headers()
    with path.open("rb") as file_obj:
        shutil.copyfileobj(file_obj, handler.wfile)
